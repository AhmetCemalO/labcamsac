import numpy as np
from vimba import *
from .generic_cam import GenericCam
from utils import display

def AVT_get_ids():
    with Vimba.get_instance() as vimba:
        cams = vimba.get_all_cameras()
        cam_ids = []
        cam_infos = []
        for cam in cams:
            cam_ids.append(cam.get_id())
            cam_infos.append('{0} {1} {2}'.format(cam.get_model(),
                                                  cam.get_serial(),
                                                  cam.get_id()))
    return cam_ids, cam_infos


class AVTCam(GenericCam):
    def __init__(self, cam_id = None, params = None, format = None):
    
        super().__init__(name = 'PCO', cam_id = cam_id, params = params, format = format)
        
        default_params = {'exposure':29000, 'frame_rate':30,'gain':10,
                          'frame_timeout':100, 'nFrameBuffers':10,
                          'triggerSource': 'Line1', 'triggerMode':'LevelHigh',
                          'triggerSelector': 'FrameStart', 'acquisitionMode': 'Continuous',
                          'nTriggeredFrames': 1000, 
                          'poll_timeout':1, 'trigger':0}
                          
        self.params = {**default_params, **self.params}
        self.params['exposure time'] = self.params.pop('exposure')

        default_format = {'dtype': np.uint8}
        self.format = {**default_format, **self.format}
        
    def __enter__(self):
        self.vimba = Vimba.get_instance()
        self.vimba.__enter__()
        self.cam_handle = self.vimba.get_camera_by_id(self.cam_id)
        self.cam_handle.__enter__()
        self.apply_settings()
        
        self._init_format()
        return self
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.cam_handle.__exit__(exc_type, exc_value, exc_traceback)
        self.vimba.__exit__(exc_type, exc_value, exc_traceback)
        
    def apply_settings(self):
        self.cam_handle.EventNotification = 'On'
        self.cam_handle.set_pixel_format(PixelFormat.Mono8)
        self.cam_handle.AcquisitionFrameRateAbs = self.params['frame_rate']
        self.cam_handle.GainRaw = self.params['gain']
        self.cam_handle.ExposureTimeAbs =  self.params['exposure time']
        self.cam_handle.SyncOutSelector = 'SyncOut1'
        self.cam_handle.SyncOutSource = 'FrameReadout'#'Exposing'
        
        self.cam_handle.TriggerSource = self.params['triggerSource'] if self.triggered else 'FixedRate'
        self.cam_handle.TriggerMode = 'On' if self.triggered else 'Off'
        self.cam_handle.AcquisitionMode = self.params['acquisitionMode'] if self.triggered else 'Continuous'
        self.cam_handle.TriggerSelector = self.params['triggerSelector'] if self.triggered else 'FrameStart'
        
        if self.triggered:
            self.cam_handle.TriggerActivation = self.params['triggerMode']
            if self.acquisitionMode == 'MultiFrame':
                self.cam_handle.AcquisitionFrameCount = self.params['nTriggeredFrames']
        else:
            display('[Cam - {0}] Using no trigger.'.format(self.cam_id))
        # display(f'AVT - configuration: {self.cam_handle.get_all_features()}')
        
    
    def record(self):
        pass
        
    def stop(self):
        pass
        
    def image(self):
        frame = self.cam_handle.get_frame()
        img = frame.as_opencv_image()
        frame_id = frame.get_id()
        timestamp = frame.get_timestamp()
        return img, (frame_id, timestamp)
    