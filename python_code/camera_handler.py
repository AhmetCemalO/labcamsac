from multiprocessing import Process,Queue,Event,Array,Value
import numpy as np
import ctypes
import time
from cams.avt_cam import AVTCam
from cams.pco_cam import PCOCam
from file_writer import BinaryWriter, TiffWriter, FFMPEGWriter, OpenCVWriter
from utils import display

class CameraHandler(Process):
    
    def __init__(self, cam_dict, writer_dict):
        super().__init__()
        
        self.cam_dict = cam_dict
        self.writer_dict = writer_dict
        
        self.close_event = Event()
        self.start_trigger = Event()
        self.is_running = Event()
        self.stop_trigger = Event()
        self.camera_ready = Event()
        self.eventsQ = Queue()
        self.saving = Event()
        self.nframes = Value('i',0)
        
        self.img = None
        
        self.lastframeid = -1
        self.lasttime = 0
        
        self._init_framebuffer()
        
    def _init_framebuffer(self):
        with self._open_cam() as cam:
            dtype  = cam.format.get('dtype', None)
            height = cam.format.get('height', None)
            width  = cam.format.get('width', None)
            n_chan = cam.format.get('n_chan', 1)
            
            
            
            if dtype == np.uint8:
                cdtype = ctypes.c_ubyte
            elif dtype == np.uint16:
                cdtype = ctypes.c_ushort
            else:
                display(f"WARNING: dtype {dtype} not available, defaulting to np.uint16")
                cdtype = ctypes.c_ushort
            
            if (dtype is None) or (height is None) or (width is None):
                display(f"ERROR: format (height, width, dtype[,n_chan]) needs to be set to init the framebuffer")
                return

            self.frame = Array(cdtype,np.zeros([height, width, n_chan],
                                               dtype = dtype).flatten())
            self.format = {'dtype':dtype, 'height':height,'width':width,'n_chan':n_chan,'cdtype':cdtype}
            
            self._init_buffer()
            
    def _init_buffer(self):
        self.img = np.frombuffer(self.frame.get_obj(), dtype = self.format['cdtype'])\
                        .reshape([self.format['height'], self.format['width'], self.format['n_chan']])
                        
    def run(self):
        self._init_buffer()
        with self._open_writer() as writer:
            with self._open_cam() as cam:
                while not self.close_event.is_set():
                    self.init_run()
                    display(f'[{cam.name} {cam.cam_id}] waiting for trigger.')
                    self.wait_for_trigger()
                    cam.record()
                    while not self.stop_trigger.is_set():
                        frame, metadata = cam.image()
                        if self.saving.is_set():
                            writer.save(frame, metadata)
                        self._update(frame,metadata)
                    display('[Camera] Stop trigger set.')
                    self.close_run()
    
    def _open_writer(self):
        writer_dict_copy = self.writer_dict.copy()
        writer_type = writer_dict_copy.pop('writer', 'opencv')
        writers = {'opencv': OpenCVWriter, 'binary': BinaryWriter, 'tiff': TiffWriter, 'ffmpeg': FFMPEGWriter} 
        writer = writers[writer_type]
        std_keys = ['filename', 'dataname', 'datafolder', 'pathformat', 'frames_per_file'] 
        dict = {key: writer_dict_copy[key] for key in writer_dict_copy if key in std_keys}
        return writer(**dict)
    
    def _open_cam(self):
        cam_dict_copy = self.cam_dict.copy()
        cam_type = cam_dict_copy.pop('driver', 'avt').lower()
        cameras = {'avt': AVTCam, 'pco': PCOCam} 
        camera = cameras[cam_type]
        return camera(cam_id = cam_dict_copy.get('id', None),
                      params = cam_dict_copy.get('params', None))
    
    def get_image(self):
        return self.img
        
    def init_run(self):
        self.nframes.value = 0
        self.lastframeid = -1
        self.camera_ready.set()
    
    def close_run(self):
        self.start_trigger.clear()
        if not self.close_event.is_set():
            self.stop_trigger.clear()
        self.is_running.clear()
        
    def _update(self, frame, metadata):
        self._update_buffer(frame)
        self.nframes.value += 1
        frameID,timestamp = metadata[:2]
        self.lastframeid = frameID
        self.lasttime = timestamp
    
    def _update_buffer(self,frame):
        self.img[:] = np.reshape(frame,self.img.shape)[:]
    
    def wait_for_trigger(self):
        while not self.start_trigger.is_set() and not self.stop_trigger.is_set():
            # limits resolution to 1 ms
            time.sleep(0.001)
        self.is_running.set()
        self.camera_ready.clear()
    
    def start_saving(self):
        self.saving.set()
        
    def stop_saving(self):
        self.saving.clear()
    
    def start_acquisition(self):
        if self.camera_ready.is_set():
            self.start_trigger.set()
            return True
        print("Could not start acquisition, camera not ready")
        return False
        
    def stop_acquisition(self):
        self.stop_trigger.set()

    def close(self):
        self.close_event.set()
        self.stop_acquisition()
        