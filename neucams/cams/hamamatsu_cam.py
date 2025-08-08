# neucams/cams/hamamatsu_cam.py
from __future__ import annotations
import logging, time
from typing import List, Optional, Tuple
import numpy as np

# pyDCAM
from pyDCAM import dcamapi_init, dcamapi_uninit, HDCAM
from pyDCAM.dcamprop import DCAMIDPROP
from pyDCAM.dcamapi_enum import DCAM_IDSTR

from .generic_cam import GenericCam

LOG = logging.getLogger(__name__)


class _DCAMRuntime:
    _booted = False
    _ref = 0

    def __enter__(self):
        if not self._booted:
            dcamapi_init()
            self._booted = True
        self._ref += 1
        return self

    def __exit__(self, exc_type, exc, tb):
        self._ref -= 1
        if self._booted and self._ref <= 0:
            try:
                dcamapi_uninit()
            finally:
                self._booted = False
                self._ref = 0

    @staticmethod
    def list_camera_ids() -> List[str]:
        ids: List[str] = []
        cold = not _DCAMRuntime._booted
        if cold:
            count = dcamapi_init()
        else:
            count = dcamapi_init()
        try:
            for i in range(count):
                with HDCAM(i) as cam:
                    ids.append(cam.dcamdev_getstring(DCAM_IDSTR.DCAM_IDSTR_CAMERAID))
        finally:
            if cold:
                dcamapi_uninit()
        return ids


class HamamatsuCam(GenericCam):
    """
    DCAM-API backend via pyDCAM.
    - Selects device by serial_number (preferred) or falls back to first.
    - Starts acquisition in __enter__ (to match your other drivers).
    """

    def __init__(
        self,
        cam_id: int | None = None,        # ignored; we use serial_number
        params: dict | None = None,
        format: dict | None = None,
        *,
        exposure_time: float | None = None,   # float sec or int microseconds
        frame_count: int = 0,
        serial_number: str | None = None,
    ):
        super().__init__(name="Hamamatsu", cam_id=None, params=params, format=format)
        self._rt = _DCAMRuntime()
        self._cam: Optional[HDCAM] = None
        self._wait = None
        self._bufs = max(3, frame_count or 10)
        self._frame_idx = 0

        self.serial_number = serial_number
        self.exposure_time = exposure_time
        self.frame_count = frame_count or 10
        self.ready = False

        # for handler framebuffer init
        self.format.setdefault("dtype", np.uint16)
        self.exposed_params = ["exposure", "binning"]

    # ------------ lifecycle ------------
    def __enter__(self):
        self._rt.__enter__()
        idx = self._resolve_camera_index()
        self._cam = HDCAM(idx).__enter__()
        LOG.info("Hamamatsu camera opened: %s",
                 self._cam.dcamdev_getstring(DCAM_IDSTR.DCAM_IDSTR_MODEL))

        # format before starting
        self._query_format()

        # parameters
        if self.exposure_time is not None:
            self._try_set("exposure_time", self.exposure_time)
        self.apply_params()

        # allocate & start
        self._cam.dcambuf_alloc(self._bufs)
        self._wait = self._cam.dcamwait_open()
        self._cam.dcamcap_start()
        self.is_recording = True
        self._frame_idx = 0
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.stop()
        finally:
            if self._cam is not None:
                self._cam.__exit__(exc_type, exc_val, exc_tb)
                self._cam = None
            self._rt.__exit__(exc_type, exc_val, exc_tb)
        return False

    def stop(self):
        if self._cam is None:
            return
        try:
            if self.is_recording:
                self._cam.dcamcap_stop()
        except Exception:
            pass
        finally:
            self.is_recording = False
        try:
            self._cam.dcambuf_release()
        except Exception:
            pass
        self._wait = None

    # ------------ acquisition ------------
    def image(self) -> Tuple[Optional[np.ndarray], str | Tuple[int, float]]:
        if not self.is_recording or self._cam is None or self._wait is None:
            return None, "not recording"
        try:
            self._wait.dcamwait_start(timeout=1000)  # ms
            frame = self._cam.dcambuf_copyframe()
            if frame is None or frame.size == 0:
                return None, "timeout"
            if "height" not in self.format:
                self._set_format_from_frame(frame)
            meta = (self._frame_idx, time.time())
            self._frame_idx += 1
            return frame, meta
        except Exception as e:
            LOG.error("Hamamatsu acquisition error: %r", e)
            return None, f"acquisition error: {e}"

    # ------------ params / format ------------
    def _query_format(self):
        w = int(self._cam.dcamprop_getvalue(DCAMIDPROP.DCAM_IDPROP_IMAGE_WIDTH))
        h = int(self._cam.dcamprop_getvalue(DCAMIDPROP.DCAM_IDPROP_IMAGE_HEIGHT))
        self.format.update({
            "width":  w,
            "height": h,
            "n_chan": 1,
            "dtype":  np.uint16,  # numpy dtype object (camera gives 16-bit)
        })
        self.ready = True

    def _set_format_from_frame(self, frame: np.ndarray):
        h, w = frame.shape[:2]
        self.format["height"] = int(h)
        self.format["width"]  = int(w)
        self.format["n_chan"] = frame.shape[2] if frame.ndim == 3 else 1
        self.format["dtype"]  = frame.dtype

    def apply_params(self):
        if self._cam is None or not self.params:
            return
        for k, v in self.params.items():
            self._try_set(k.lower(), v)

    def _try_set(self, key: str, val) -> bool:
        try:
            if key in ("exposure", "exposure_time"):
                secs = float(val) / 1e6 if isinstance(val, (int, np.integer)) else float(val)
                self._cam.dcamprop_setvalue(DCAMIDPROP.DCAM_IDPROP_EXPOSURETIME, secs)
                return True
            if key == "binning":
                self._cam.dcamprop_setvalue(DCAMIDPROP.DCAM_IDPROP_BINNING, int(val))
                return True
            # add more DCAM props here as needed
            return False
        except Exception:
            return False

    # ------------ discovery ------------
    def _resolve_camera_index(self) -> int:
        count = dcamapi_init()
        if count <= 0:
            raise RuntimeError("No Hamamatsu cameras detected.")
        if self.serial_number:
            for i in range(count):
                with HDCAM(i) as cam:
                    camid = cam.dcamdev_getstring(DCAM_IDSTR.DCAM_IDSTR_CAMERAID)
                    if str(self.serial_number) in str(camid):
                        return i
            raise RuntimeError(f"No Hamamatsu camera with serial '{self.serial_number}' found.")
        return 0

    # ------------ misc ------------
    def is_connected(self) -> bool:
        try:
            with self._rt:
                if self.serial_number:
                    try:
                        self._resolve_camera_index()
                        return True
                    except Exception:
                        return False
                return dcamapi_init() > 0
        except Exception:
            return False

    @staticmethod
    def list_cameras() -> List[str]:
        return _DCAMRuntime.list_camera_ids()
