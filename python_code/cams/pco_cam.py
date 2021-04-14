"""pco_cam.py
"""
import time
import numpy as np
import pco
from cams.generic_cam import GenericCam
from utils import display

class PCOCam(GenericCam):
    def __init__(self, cam_id = None, params = None, format = None):
        
        cam_id = 0 # the cam_id is discarded for PCOCam, the pco.Camera class does not allow specific opening
        # it is possible to select specific interface/camera id via sdk (or by adjusting init of Camera), 
        # since we don't use multiple PCO's per setup, I will keep it simple
        
        super().__init__(name = 'PCO', cam_id = cam_id, params = params, format = format)
        
        default_params = {'exposure':15, 'triggerSource': 'external exposure start & software trigger',
                          'poll_timeout':1, 'trigger':0}
                          
                            # 'triggerSource' options
                            # * 'auto sequence'
                            # * 'software trigger'
                            # * 'external exposure start & software trigger'
                            # * 'external exposure control'
                            # * 'external synchronized'
                            # * 'fast external exposure control'
                            # * 'external CDS control'
                            # * 'slow external exposure control'
                            # * 'external synchronized HDSDI'
        self.params = {**default_params, **self.params}
        self.params['exposure time'] = self.params.pop('exposure')/1000

        default_format = {'dtype': np.uint16}
        self.format = {**default_format, **self.format}
    
    def is_connected(self):
        """To be checked before trying to open"""
        try:
            cam = pco.Camera()
            cam.close()
            display('PCO cam detected.')
            return True
        except ValueError:
            display('PCO cam not detected.')
            return False
        
    def __enter__(self):
        self.cam_handle = pco.Camera()
        self.cam_handle.__enter__()
        self.apply_settings()
        self._record()
        self._init_format()
        return self
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()
        self.cam_handle.__exit__(exc_type, exc_value, exc_traceback)
        return True
        
    def close(self):
        self.cam_handle.close()

    def apply_settings(self):
        self.params['trigger'] = self.params['triggerSource'] if self.triggered else 'auto sequence'
        self.cam_handle.configuration = self.params
        display(f'PCO - configuration: {self.cam_handle.configuration}')
        
    def _record(self):
        self.cam_handle.record(number_of_images=10, mode = 'fifo')

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
