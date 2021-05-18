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
    timeout = 2000
    def __init__(self, cam_id = None, params = None, format = None):
        
        if cam_id is None:
            ids, _ = AVT_get_ids()
            if len(ids) > 0:
                cam_id = ids[0]
                
        super().__init__(name = 'AVT', cam_id = cam_id, params = params, format = format)
        
        default_params = {'exposure':29000, 'frame_rate':30,'gain':10, 'gain_auto': False,
                          'acquisition_mode': 'Continuous', 'n_frames': 1,
                          'triggered': False, # hardware trigger
                          'triggerSource': 'Line1', 'triggerMode':'LevelHigh',
                          'triggerSelector': 'FrameStart'
                           #'frame_timeout':100,
                          }
                          
        self.exposed_params = ['frame_rate', 'gain', 'exposure', 'gain_auto', 'triggered', 'acquisition_mode', 'n_frames']
        
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
            self.cam_handle.load_settings(self.params['settings_file'], PersistType.All)
        self.apply_params()
        self._record()
        self._init_format()
        return self
        
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.cam_handle.__exit__(exc_type, exc_value, exc_traceback)
        self.vimba.__exit__(exc_type, exc_value, exc_traceback)
        return True
        
    def apply_params(self):
        
        resume_recording = self.is_recording
        if self.is_recording:
            self.stop()
            
        adjusted_params = self.params.copy() # adjust to specific interface if needed
        
        self.cam_handle.EventNotification.set('On')
        self.cam_handle.set_pixel_format(PixelFormat.Mono8)
        self.cam_handle.SyncOutSelector.set('SyncOut1')
        self.cam_handle.SyncOutSource.set('FrameReadout')#'Exposing'
        
        self.cam_handle.AcquisitionFrameRateAbs.set(adjusted_params['frame_rate'])
        self.cam_handle.Gain.set(adjusted_params['gain'])
        self.cam_handle.GainAuto.set('Once' if adjusted_params['gain_auto'] else 'Off')
        
        self.cam_handle.ExposureTimeAbs.set(adjusted_params['exposure'])
        
        # self.cam_handle.TriggerMode.set('On' if adjusted_params['triggered'] else 'Off')
        # self.cam_handle.TriggerSelector.set(adjusted_params['triggerSelector'] if adjusted_params['triggered'] else 'FrameStart')
        # self.cam_handle.TriggerSource.set(adjusted_params['triggerSource'] if adjusted_params['triggered'] else 'FixedRate')
        
        self.cam_handle.ExposureMode.set('Timed')
        
        # self.cam_handle.AcquisitionMode.set(adjusted_params['acquisition_mode'])
        # if adjusted_params['acquisition_mode'] == 'MultiFrame':
            # self.cam_handle.AcquisitionFrameCount.set(adjusted_params['n_frames'])
            
        # if adjusted_params['triggered']:
            # self.cam_handle.TriggerActivation.set(adjusted_params['triggerMode'])
            # display(f'[{self.name} {self.cam_id}] Using network trigger.')
        
        if resume_recording:
            self._record()

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
        limit = self.params['n_frames'] if self.params['acquisition_mode'] == "MultiFrame" else None
        self.frame_generator = self.cam_handle.get_frame_generator(limit = limit, timeout_ms = self.timeout)
        self.is_recording = True
        
    def stop(self):
        self.cam_handle.AcquisitionStop.run()
        while not self.cam_handle.AcquisitionStop.is_done():
            time.sleep(0.01)
        self.is_recording = False
        
    def image(self):
        try:
            frame = next(self.frame_generator) if hasattr(self, 'frame_generator') else self.cam_handle.get_frame(timeout_ms = self.timeout)
            img = frame.as_opencv_image()
            frame_id = frame.get_id()
            timestamp = frame.get_timestamp()
            return img, (frame_id, timestamp)
        except StopIteration:
            return None, "stop"
        except VimbaTimeout:
            return None, "timeout"
      