from __future__ import annotations
"""
Hamamatsu camera wrapper that plugs into the project s GenericCam base-class
using Hamamatsus DCAM-API Python bindings (`pip install hamamatsu`).
"""

import logging
import time
from typing import List, Optional, Tuple

import numpy as np

# Third-party SDK   thin wrapper around Hamamatsu s DCAM runtime
try:
    from hamamatsu.dcam import dcam, copy_frame, Stream
except ModuleNotFoundError as exc:
    dcam = None
    copy_frame = None
    Stream = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

# Your own abstraction layer
from neucams.cams.generic_cam import GenericCam

LOG = logging.getLogger(__name__)


class _DCAMRuntime:
    """Singleton, ref-counted context-manager for the global DCAM API."""
    _booted: bool = False
    _refcount: int = 0
    _lock: bool = False

    def __enter__(self):
        if _IMPORT_ERROR:
            raise RuntimeError(
                "hamamatsu package not installed   run `pip install hamamatsu`"
            ) from _IMPORT_ERROR
        
        # --- FIX START: Remove the dangerous timeout loop ---
        # If the lock is held, it indicates a programming error (unclean shutdown)
        # from a previous run. Failing fast is better than hanging for 15 seconds.
        if self._lock:
            raise RuntimeError("DCAMRuntime lock is held. A previous camera process may have crashed without cleaning up.")
        
        if not self._booted:
            try:
                dcam.__enter__()
                self._booted = True
            except Exception as e:
                LOG.debug("DCAM runtime init failed: %r", e)
                raise
        self._refcount += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._booted:
            self._refcount -= 1
            if self._refcount <= 0:
                self._lock = True
                try:
                    dcam.__exit__(exc_type, exc_val, exc_tb)
                except Exception as e:
                    LOG.debug("DCAM runtime cleanup failed: %r", e)
                finally:
                    self._booted = False
                    self._refcount = 0
                    self._lock = False

    @staticmethod
    def list_camera_ids() -> List[int]:
        if _IMPORT_ERROR:
            return []
        if _DCAMRuntime._booted:
            return list(range(len(dcam)))
        dcam.__enter__()
        try:
            return list(range(len(dcam)))
        finally:
            dcam.__exit__(None, None, None)


class HamamatsuCam(GenericCam):
    """GenericCam implementation for Hamamatsu cameras via DCAM-API."""

    def __init__(
        self,
        cam_id: int | None = 0,
        params: dict | None = None,
        format: dict | None = None,
        *,
        exposure_time: float | None = None,
        frame_count: int = 0,
        serial_number: str | None = None,
    ) -> None:
        super().__init__(name="Hamamatsu", cam_id=cam_id, params=params, format=format)
        if _IMPORT_ERROR:
            raise RuntimeError("Hamamatsu SDK or its Python wrapper missing.")

        self._rt = _DCAMRuntime()
        self._cam = None
        self._stream = None # This will be our persistent stream iterator
        self.exposure_time = exposure_time
        self.frame_count = frame_count or 10
        self.serial_number = serial_number
        self.ready = False

    def __enter__(self):
        self._rt.__enter__()
        idx = self._resolve_camera_index()
        self._cam = dcam[idx].__enter__()

        try:
            # --- FIX START: Apply parameters before querying the format ---
            # Set exposure first as it's a critical parameter.
            if self.exposure_time is not None:
                self._try_set("exposure_time", float(self.exposure_time))
            
            # Apply all other parameters from the config file.
            self.apply_params()
            time.sleep(0.1) # A small, safe delay for settings to propagate in hardware.
            
            LOG.info("Hamamatsu camera opened: %s", self._cam.info)

            # Replace the unreliable warmup with a direct query.
            self._query_and_set_format()
            
            # The 'ready' flag is now set based on a successful query, not a test frame.
            self.ready = True
            LOG.info("Camera is ready. Format: %s", self.format)
            # --- FIX END ---

        except Exception as e:
            LOG.error("Failed to initialize Hamamatsu camera: %r", e, exc_info=True)
            # Ensure resources are cleaned up on failure.
            self.__exit__(type(e), e, e.__traceback__)
            # Re-raise the exception so the CameraHandler knows initialization failed.
            raise
            
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


    def start(self):
        if not self.ready: raise RuntimeError("Cannot start: Camera is not ready.")
        if self.is_recording: return
        self.stop()
        try:
            # SOLUTION: Re-apply parameters to ensure the camera is in a correct state
            # before starting the main acquisition.
            LOG.info("Applying parameters before starting acquisition...")
            self.apply_params()
            time.sleep(0.05)  # A small delay to allow settings to apply

            # The rest of the method remains the same
            self._stream = Stream(self._cam, self.frame_count)
            self._stream.__enter__()
            self._cam.start()
            self.is_recording = True
            LOG.info("Acquisition started.")
        except Exception as e:
            LOG.error("Failed to start acquisition: %r", e)
            self.stop()
            raise

    def stop(self):
        if self._cam is None: return
        try:
            if self.is_recording or self._stream is not None:
                self._cam.stop()
        except Exception: pass
        finally: self.is_recording = False
        if self._stream is not None:
            try: self._stream.__exit__(None, None, None)
            except Exception: pass
            finally: self._stream = None

    def image(self) -> Tuple[Optional[np.ndarray], str]:
        if not self.is_recording or self._stream is None:
            return None, "not recording"
        try:
            # CORRECT WAY: Get the next buffer from the stream iterator and copy it.
            buf = next(self._stream)
            frame = copy_frame(buf)
            return frame, "OK"
        except StopIteration:
            # This can happen if the stream is stopped between the is_recording check and next()
            return None, "stream ended"
        except Exception as e:
            LOG.error("Frame acquisition failed: %r", e)
            return None, f"acquisition error: {str(e)}"

    def _query_and_set_format(self):
        """
        Directly queries the camera for its current image format settings.
        This is far more reliable than the old warmup acquisition.
        """
        if self._cam is None:
            raise RuntimeError("Cannot query format, camera is not open.")

        try:
            # --- FIX START: Query properties directly from the camera object ---
            # NOTE: The property names might vary slightly based on the dcam library version.
            # Common properties are 'image_width', 'image_height', 'image_pixel_format'.
            # We access them using the dictionary-style getter.
            w = self._cam['image_width'].value
            h = self._cam['image_height'].value
            
            # The pixel format is usually an enum, so we need to map it.
            pixel_format_enum = self._cam['pixel_format'].value
            
            if 'MONO8' in pixel_format_enum:
                dtype_str = 'uint8'
            elif 'MONO16' in pixel_format_enum:
                dtype_str = 'uint16'
            elif 'MONO12' in pixel_format_enum: # DCAM often uses 12 or 14-bit, stored in uint16
                dtype_str = 'uint16'
            else:
                # Add other formats if needed, but default to uint16 as a safe bet.
                LOG.warning(f"Unknown pixel format '{pixel_format_enum}'. Defaulting to uint16.")
                dtype_str = 'uint16'

            self.format["height"] = int(h)
            self.format["width"] = int(w)
            self.format["n_chan"] = 1 # Assuming mono cameras for now
            self.format["dtype"] = dtype_str
            # --- FIX END ---
            
        except Exception as e:
            LOG.error("Failed to query camera format properties: %r", e)
            raise RuntimeError("Could not determine camera image format.") from e

    def _warmup_and_set_format(self, timeout_s: float = 3.0):
        if self._cam is None: return
        tmp_stream = None
        try:
            # Create a temporary stream; its constructor handles buffers.
            tmp_stream = Stream(self._cam, 3)
            tmp_stream.__enter__()
            self._cam.start()

            deadline = time.time() + timeout_s
            frame = None
            while time.time() < deadline:
                try:
                    # Get a frame using the correct iterator pattern
                    buf = next(tmp_stream)
                    frame = copy_frame(buf)
                    if frame is not None:
                        break
                except Exception:
                    time.sleep(0.01)

            if frame is not None:
                self._set_format_from_frame(frame)
                self.ready = True
            else:
                self.ready = False
        except Exception as e:
            LOG.error("Warm-up failed with exception: %r", e)
            self.ready = False
        finally:
            # Clean up the temporary session
            try: self._cam.stop()
            except Exception: pass
            if tmp_stream is not None:
                try: tmp_stream.__exit__(None, None, None)
                except Exception: pass

    def _set_format_from_frame(self, frame: np.ndarray):
        h, w = frame.shape[:2]
        self.format["height"] = int(h)
        self.format["width"] = int(w)
        self.format["n_chan"] = frame.shape[2] if frame.ndim == 3 else 1
        self.format["dtype"] = str(frame.dtype)

    def apply_params(self):
        if self._cam is None or not self.params: return
        for k, v in self.params.items():
            self._try_set(k.lower(), v)

    def _try_set(self, key: str, val) -> bool:
        if key == "exposure": key = "exposure_time"
        if key == "exposure_time":
            val = float(val) / 1e6 if isinstance(val, (int, np.integer)) else float(val)
        try:
            self._cam[key] = val
            return True
        except Exception: return False

    def _resolve_camera_index(self) -> int:
        if len(dcam) == 0: raise RuntimeError("No Hamamatsu cameras detected.")
        if self.serial_number:
            for i in range(len(dcam)):
                with dcam[i] as cam:
                    if any(str(self.serial_number) in str(v) for v in getattr(cam, "info", {}).values()):
                        return i
            raise RuntimeError(f"No camera with serial '{self.serial_number}' found.")
        idx = 0 if self.cam_id is None else int(self.cam_id)
        if not (0 <= idx < len(dcam)):
            raise RuntimeError(f"cam_id {idx} out of range (0..{len(dcam)-1}).")
        return idx
        
    def is_connected(self) -> bool:
        try:
            with self._rt:
                return len(dcam) > 0
        except: return False

    @staticmethod
    def list_cameras() -> List[int]:
        return _DCAMRuntime.list_camera_ids()