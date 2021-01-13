"""cams.py
Camera classes for behavioral monitoring and single photon imaging.
Creates separate processes for acquisition and queues frames"""
import time
import ctypes
from multiprocessing import Process,Queue,Event,Array,Value
import numpy as np
from .utils import display

class GenericCam(Process):
    """Generic class for interfacing with the cameras
    Has last frame on multiprocessing array
    """
    def __init__(self, name = '', cam_id = None, outQ = None, recorderpar = None, refreshperiod = 1/20., params = None, format = None):
        
        if cam_id is None:
            display('Need to supply a camera ID.')
            raise
            
        super().__init__()
        
        self.params = params if params is not None else {}
        self.format = format if format is not None else {}
        
        self.name = name
        self.cam = None
        self.cam_id = cam_id
        self.close_event = Event()
        self.start_trigger = Event()
        self.stop_trigger = Event()
        self.saving = Event()
        self.nframes = Value('i',0)
        self.queue = outQ
        self.camera_ready = Event()
        self.eventsQ = Queue()
        self._init_controls()
        self._init_ctrevents()
        self.cam_is_running = False
        self.was_saving=False
        self.recorderpar = recorderpar
        self.recorder = None
        self.refresh_period = refreshperiod
        self._tupdate = time.time()
        self.daemon = True
        self.lasttime = 0
        self.frame = None
        self.img = None

    def _init_framebuffer(self):
        dtype  = self.format.get('dtype', None)
        height = self.format.get('height', None)
        width  = self.format.get('width', None)
        n_chan = self.format.get('n_chan', 1)
        
        if (dtype is None) || (height is None) ||(width is None):
            display(f"ERROR: format (height, width, dtype[,n_chan]) needs to be set to init the framebuffer")
            return

        if dtype == np.uint8:
            cdtype = ctypes.c_ubyte
        elif dtype == np.uint16:
            cdtype = ctypes.c_ushort
        else:
            display(f"WARNING: dtype {dtype} not available, defaulting to np.uint16")
            cdtype = ctypes.c_ushort

        self.frame = Array(cdtype,np.zeros([height, width,self.nchan],
                                           dtype = dtype).flatten())
        self.img = np.frombuffer(self.frame.get_obj(),
                                 dtype = cdtype).reshape([height, width, n_chan])
    def get_img(self):
        return self.img

    def stop_saving(self):
        # This will send a stop to stop saving and close the writer.
        #if self.saving.is_set():
        self.saving.clear()

    def _init_controls(self):
        pass

    def _init_ctrevents(self):
        if hasattr(self,'ctrevents'):
            for c in self.ctrevents:
                self.ctrevents[c]['call'] = 'self.' + self.ctrevents[c]['function']

    def _start_recorder(self):
        if not self.recorderpar is None:
            extrapar = {}
            if 'binary' in self.recorderpar['recorder'].lower():
                from .io import BinaryCamWriter as rec
            elif 'tiff' in self.recorderpar['recorder'].lower():
                from .io import TiffCamWriter as rec
            elif 'ffmpeg' in self.recorderpar['recorder'].lower():
                from .io import FFMPEGCamWriter as rec
                if 'hwaccel' in self.recorderpar:
                    extrapar['hwaccel'] =  self.recorderpar['hwaccel']
            else:
                display('Recorder {0} not implemented'.format(
                    self.recorderpar['recorder']))
            if 'rec' in dir():
                self.recorder = rec(self,
                                    inQ = self.queue,
                                    filename = self.recorderpar['filename'],
                                    pathformat = self.recorderpar['pathformat'],
                                    dataname = self.recorderpar['dataname'],
                                    datafolder = self.recorderpar['datafolder'],
                                    framesperfile = self.recorderpar['framesperfile'],
                                    incrementruns = True,**extrapar)

    def run(self):
        self._init_ctrevents()
        self.img = np.frombuffer(self.frame.get_obj(),
                                 dtype = self.dtype).reshape(
                                     [self.h,self.w,self.nchan])
        self.close_event.clear()
        self._start_recorder()
        while not self.close_event.is_set():
            self._cam_init()
            if self.stop_trigger.is_set():
                break
            self._cam_waitsoftwaretrigger()
            if not self.stop_trigger.is_set():
                self._cam_startacquisition()
                self.cam_is_running = True
            while not self.stop_trigger.is_set():
                ret, frame, metadata = self._cam_loop()
                if ret:
                    self._handle_frame(frame,metadata)
                self._parse_command_queue()
                # to be able to pause acquisition on software trigger
                if not self.start_trigger.is_set() and not self.stop_trigger.is_set():
                    self._cam_stopacquisition()
                    self._cam_waitsoftwaretrigger()
                    if not self.stop_trigger.is_set():
                        self._cam_startacquisition()
                        self.cam_is_running = True
            display('[Camera] Stop trigger set.')
            self.start_trigger.clear()
            self._cam_close()
            self.cam_is_running = False
            if self.was_saving:
                self.was_saving = False
                if self.recorder is None:
                    display('[Camera] Sending stop signal to the recorder.')
                    self.queue.put(['STOP'])
                else:
                    self.recorder.close_run()
            self.stop_trigger.clear()

    def _handle_frame(self,frame,metadata):
        if self.saving.is_set():
            self.was_saving = True
            if not metadata[0] == self.lastframeid :
                if not self.recorder is None:
                    self.recorder.save(frame,metadata)
                else:
                    self.queue.put((frame,metadata))
        elif self.was_saving:
            if self.recorder is None:
                self.was_saving = False
                display('[Camera] Sending stop signal to the recorder.')
                self.queue.put(['STOP'])
            else:
                self.was_saving = False
                self.recorder.close_run()
        frameID,timestamp = metadata[:2]
        if not frameID == self.lastframeid:
            t = time.time()
            if (t - self._tupdate) > self.refresh_period:
                self._update_buffer(frame,frameID)
                self._tupdate = t
            #self.nframes.value += 1
        self.lastframeid = frameID
        self.lasttime = timestamp

    def _update_buffer(self,frame,frameID):
        self.img[:] = np.reshape(frame,self.img.shape)[:]
        
    def _parse_command_queue(self):
        if not self.eventsQ.empty():
            cmd = self.eventsQ.get()
            if '=' in cmd:
                cmd = cmd.split('=')
                if hasattr(self,'ctrevents'):
                    self._call_event(cmd[0],cmd[1])
                if cmd[0] == 'filename':
                    if not self.recorder is None:
                        if hasattr(self,'recorder'):
                            self.recorder.set_filename(cmd[1])
                    self.recorderpar['filename'] = cmd[1]
                elif cmd[0] == 'log':
                    msg = '# {0},{1} - {2}'.format(
                        self.lastframeid,
                        self.lasttime,cmd[1])
                    if self.recorder is None:
                        self.queue.put([msg])
                    else:
                        self.recorder.logfile.write(msg)

    def _call_event(self, eventname, eventvalue):
        if eventname in self.ctrevents:
            val = eval(self.ctrevents[eventname]['type']+'('+str(eventvalue)+')')
            eval(self.ctrevents[eventname]['call']+'(val)')

    def _cam_init(self):
        '''initialize the camera'''
        pass

    def _cam_startacquisition(self):
        '''start camera acq'''
        pass

    def _cam_stopacquisition(self):
        '''stop camera acq'''
        pass

    def _cam_close(self):
        '''close cam - release driver'''
        pass

    def _cam_loop(self):
        '''get a frame and move on, returns frame,(frameID,timestamp)'''
        return False, None, (None,None)

    def _cam_waitsoftwaretrigger(self):
        '''wait for software trigger'''
        display('[{0} {1}] waiting for software trigger.'.format(self.name, self.cam_id))
        while not self.start_trigger.is_set() or self.stop_trigger.is_set():
            # limits resolution to 1 ms
            time.sleep(0.001)
            if self.close_event.is_set() or self.stop_trigger.is_set():
                break
        if self.close_event.is_set() or self.stop_trigger.is_set():
            return
        self.camera_ready.clear()

    def stop_acquisition(self):
        self.stop_trigger.set()

    def close(self):
        self.close_event.set()
        self.stop_acquisition()


