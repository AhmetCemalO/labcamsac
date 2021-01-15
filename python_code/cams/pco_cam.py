"""pco_cam.py
"""
import time
import numpy as np
import pco
from .generic_cam import GenericCam
from ..utils import display

class PCOCam(GenericCam):
    def __init__(self, cam_id = None, params = None, format = None):

        default_params = {'exposure':100, 'triggerSource': np.uint16(2),
                          'poll_timeout':1, 'trigger':0}
        params = {**default_params, **params}
        params['exposure time'] = params.pop['exposure']

        default_format = {'dtype': np.uint16}
        format = {**default_format, **format}

        super().__init__(name = 'PCO', cam_id = cam_id, params = params, format = format)

        self.cam_handle = pco.Camera() #returns first pco camera it detects
                                       #possibility to select specific interface/camera id via sdk
        self.apply_settings()
        
        self.record()
        self._init_format()

    def close(self):
        self.cam_handle.close()

    def apply_settings(self):
        self.params['trigger'] = self.params['triggerSource'] if self.params['triggered'].is_set() else 0
        self.cam_handle.configuration(self.params)
        display(f'PCO - configuration: {self.cam_handle.configuration()}')
        
    def record(self):
        self.cam_handle.record()

    def stop(self):
        self.cam_handle.stop()

    def get_health_status(self):
        ret = self.cam_handle.sdk.get_camera_health_status()
        if 'status' in ret:
            display(f"PCO - Camera health status: {ret['status']}")
        if 'warning' in ret:
            display(f"PCO - Camera health warning: {ret['warning']}")
        if 'error' in ret:
            display(f"PCO - Camera health error: {ret['error']}")
            return -1
        return 0

    def image(self):
        self.cam_handle.wait_for_first_image()
        frame, meta = self.cam_handle.image()
        return frame, (meta['camera image number'], time.time())
