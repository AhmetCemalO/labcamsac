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
    """Developed with Mako G030B (works also with prosilica)
        Note that camera features (such as ExposureTimeAbs)
        are susceptible to be differently named in other AVT cameras.
        Should such a thing happen, make this class more abstract and inherit it.
    """
    def __init__(self, cam_id = None, params = None, format = None):
        
        if cam_id is None:
            ids, _ = AVT_get_ids()
            if len(ids) > 0:
                cam_id = ids[0]
                
        super().__init__(name = 'AVT', cam_id = cam_id, params = params, format = format)
        
        default_params = {'exposure':29000, 'frame_rate':30,'gain':10,
                          'frame_timeout':100, 'nFrameBuffers':10,
                          'triggerSource': 'Line1', 'triggerMode':'LevelHigh',
                          'triggerSelector': 'FrameStart', 'acquisitionMode': 'Continuous',
                          'nTriggeredFrames': 1000, 
                          'poll_timeout':1, 'trigger':0, 'gain_auto': False
                          }
                          
        self.params = {**default_params, **self.params}

        default_format = {'dtype': np.uint8}
        self.format = {**default_format, **self.format}
    
    def is_connected(self):
        """To be checked before trying to open"""
        ids, _ = AVT_get_ids()
        if len(ids) == 0:
            display('No AVT cams detected, check connections.')
            return False
        display(f'AVT cams detected: {ids}')
        if self.cam_id in ids:
            display(f'Requested AVT cam detected {self.cam_id}.')
            return True
        display(f'Requested AVT cam not detected {self.cam_id}, check connections.')
        return False
        
    def __enter__(self):
        self.vimba = Vimba.get_instance()
        self.vimba.__enter__()
        self.cam_handle = self.vimba.get_camera_by_id(self.cam_id)
        self.cam_handle.__enter__()
        if 'settings_file' in self.params:
            self._init_settings()
        self.apply_params()
        self._record()
        self._init_format()
        return self

    def _init_settings(self):
        self.cam_handle.load_settings(self.params['settings_file'], PersistType.All)
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.cam_handle.__exit__(exc_type, exc_value, exc_traceback)
        self.vimba.__exit__(exc_type, exc_value, exc_traceback)
        return True
        
    def apply_params(self):
        self.cam_handle.EventNotification.set('On')
        self.cam_handle.set_pixel_format(PixelFormat.Mono8)
        self.cam_handle.SyncOutSelector.set('SyncOut1')
        self.cam_handle.SyncOutSource.set('FrameReadout')#'Exposing'
        
        self.cam_handle.AcquisitionFrameRateAbs.set(self.params['frame_rate'])
        self.cam_handle.Gain.set(self.params['gain'])
        self.cam_handle.GainAuto.set('Once' if self.params['gain_auto'] else 'Off')
        
        self.cam_handle.ExposureTimeAbs.set(self.params['exposure'])
        
        self.cam_handle.TriggerMode.set('On' if self.triggered else 'Off')
        self.cam_handle.TriggerSelector.set(self.params['triggerSelector'] if self.triggered else 'FrameStart')
        self.cam_handle.TriggerSource.set(self.params['triggerSource'] if self.triggered else 'FixedRate')
        
        self.cam_handle.AcquisitionMode.set(self.params['acquisitionMode'] if self.triggered else 'Continuous')
        self.cam_handle.ExposureMode.set('Timed')
        
        if self.triggered:
            self.cam_handle.TriggerActivation.set(self.params['triggerMode'])
            if self.params['acquisitionMode'] == 'MultiFrame':
                self.cam_handle.AcquisitionFrameCount.set(self.params['nTriggeredFrames'])
        else:
            display(f'[{self.name} {self.cam_id}] Using no trigger.')

    def get_features(self):
        features_str = ""
        features = self.cam_handle.get_all_features()
        for feature in features:
            try:
                value = feature.get()
            except (AttributeError, VimbaFeatureError):
                value = None
            features_str += '--- Feature name   : {}\n'.format(feature.get_name()) +\
                            '/// Display name   : {}\n'.format(feature.get_display_name()) +\
                            '/// Tooltip        : {}\n'.format(feature.get_tooltip()) +\
                            '/// Description    : {}\n'.format(feature.get_description()) +\
                            '/// SFNC Namespace : {}\n'.format(feature.get_sfnc_namespace()) +\
                            '/// Unit           : {}\n'.format(feature.get_unit()) +\
                            '/// Value          : {}\n\n'.format(str(value))
        return features_str

    def _record(self):
        self.cam_handle.AcquisitionStart.run()
        while not self.cam_handle.AcquisitionStart.is_done():
            time.sleep(0.01)
        self.frame_generator = self.cam_handle.get_frame_generator()
        
    def stop(self):
        self.cam_handle.AcquisitionStop.run()
        while not self.cam_handle.AcquisitionStop.is_done():
            time.sleep(0.01)
        pass
        
    def image(self):
        if hasattr(self, 'frame_generator'):
            frame = next(self.frame_generator)
        else:
            frame = self.cam_handle.get_frame()
        img = frame.as_opencv_image()
        frame_id = frame.get_id()
        timestamp = frame.get_timestamp()
        return img, (frame_id, timestamp)
    