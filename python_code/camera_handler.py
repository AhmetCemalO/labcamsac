from multiprocessing import Process,Queue,Event,Array,Value
import numpy as np
from .file_writer import BinaryWriter, TiffWriter, FFMPEGWriter, OpenCVWriter

class CameraHandler(Process):
    
    def __init__(self, cam_dict, writer_dict):
    
        self.cam_dict = cam_dict
        self.writer_dict = writer_dict
        
        self.close_event = Event()
        self.start_trigger = Event()
        self.stop_trigger = Event()
        self.camera_ready = Event()
        self.eventsQ = Queue()
        self.saving = Event()
        self.nframes = Value('i',0)
        
        self.lastframeid = -1
        self.lasttime = 0
        
        self.daemon = True
        
    def _init_framebuffer(self, format):
        dtype  = format.get('dtype', None)
        height = format.get('height', None)
        width  = format.get('width', None)
        n_chan = format.get('n_chan', 1)
        
        if dtype == np.uint8:
            cdtype = ctypes.c_ubyte
        elif dtype == np.uint16:
            cdtype = ctypes.c_ushort
        else:
            display(f"WARNING: dtype {dtype} not available, defaulting to np.uint16")
            cdtype = ctypes.c_ushort
        
        self.format['cdtype'] = cdtype
        
        if (dtype is None) or (height is None) or (width is None):
            display(f"ERROR: format (height, width, dtype[,n_chan]) needs to be set to init the framebuffer")
            return

        self.frame = Array(cdtype,np.zeros([height, width, nchan],
                                           dtype = dtype).flatten())
                                           
        self.img = np.frombuffer(self.frame.get_obj(), dtype = self.cam.format['cdtype'])\
                    .reshape([self.cam.format['height'],self.cam.format['width'], self.cam.format['n_chan']])
                    
        display("Initialized framebuffer from camera (name: {0})".format(self.name))
        
    def run(self):
        with self._open_writer() as writer:
            with self._open_cam() as cam:
                self._init_framebuffer(cam.format)
                while not close_event.is_set():
                    self.init_run()
                    self.wait_for_trigger()
                    cam.record()
                    while not self.stop_trigger.is_set():
                        frame, metadata = cam_image()
                        if not metadata[0] == self.lastframeid :
                            if self.saving.is_set():
                                writer.save((frame, metadata))
                            self._update(frame,metadata)
                    display('[Camera] Stop trigger set.')
                    writer.close_run()
                    self.close_run()
    
    def _open_writer(self):
        writer_dict_copy = self.writer_dict.copy()
        writer_type = writer_dict_copy.pop('writer', 'opencv')
        writers = {'opencv': OpenCVWriter, 'binary': BinaryCamWriter, 'tiff': TiffCamWriter, 'ffmpeg': FFMPEGCamWriter} 
        writer = writers[writer_type]
        std_keys = ['filename', 'dataname', 'datafolder', 'pathformat', 'frames_per_file'] 
        dict = {key: writer_dict_copy[key] for key in std_keys}
        return writer(**dict)
                                    
    def init_run(self):
        self.nframes.value = 0
        self.lastframeid = -1
        self.start_trigger.clear()
        self.stop_trigger.clear()
        self.camera_ready.set()
    
    def close_run(self):
        self.start_trigger.clear()
        
    def _update(self, frame, metadata):
        self._update_buffer(frame)
        self.nframes.value += 1
        frameID,timestamp = metadata[:2]
        self.lastframeid = frameID
        self.lasttime = timestamp
    
    def _update_buffer(self,frame):
        self.img[:] = np.reshape(frame,self.img.shape)[:]
        
    def wait_for_trigger(self):
        display('[{0} {1}] waiting for trigger.'.format(self.name, self.cam_id))
        while not self.start_trigger.is_set() or self.stop_trigger.is_set():
            # limits resolution to 1 ms
            time.sleep(0.001)
        self.camera_ready.clear()
        
    def stop_saving(self):
        self.saving.clear()
    
    def stop_acquisition(self):
        self.stop_trigger.set()

    def close(self):
        self.stop_acquisition()
        self.close_event.set()