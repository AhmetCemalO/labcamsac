"""cams.py
Camera classes for behavioral monitoring and single photon imaging.
Creates separate processes for acquisition and queues frames"""
import time
import ctypes

import numpy as np
from ..utils import display

class GenericCam:
    """Generic class for interfacing with the cameras
    Has last frame on multiprocessing array
    """
    def __init__(self, name = '', cam_id = None, params = None, format = None):
        
        if cam_id is None:
            display('Need to supply a camera ID.')
            raise
        
        self.name = name
        self.cam_id = cam_id
        self.cam_handle = None
        
        self.params = params if params is not None else {}
        self.format = format if format is not None else {}
        
        self.is_acquiring = False
    
    def _init_format(self):
        frame, _ = self.image()
        self.format['height'] = frame.shape[0]
        self.format['width'] = frame.shape[1]
        display(f"{self.name} - size: {self.format['height']} x {self.format['width']}")
        
    def __enter__(self):
        return self
        
    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        '''close cam - release driver'''
        pass
    
    def apply_settings(self, cam):
        pass
        
    def record(self):
        '''start camera acq'''
        pass

    def stop(self):
        '''stop camera acq'''
        pass
    
    def get_health_status(self):
        pass
    
    def image(self):
        pass

