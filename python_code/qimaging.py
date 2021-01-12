"""qimaging.py
QImaging cameras
"""

from .generic_cam import GenericCam
from .qimaging_dll import *
from .utils import display

class QImagingCam(GenericCam):
    def __init__(self, cam_id = None,
                 outQ = None,
                 exposure = 100000,
                 gain = 3500,frameTimeout = 100,
                 nFrameBuffers = 1,
                 binning = 2,
                 triggerType = 0,
                 triggered = Event(),
                 recorderpar = None):
        '''
        Qimaging camera (tested with the Emc2 only!)
            triggerType (0=freerun,1=hardware,5=software)
        '''
        frame_rate = 1./(self.exposure/1000.)
        super().__init__(name = 'Qcam', cam_id = cam_id, outQ = outQ,
                         params = {'binning': binning, 'exposure': exposure,
                                   'gain': gain, 'frame_rate': frame_rate},
                         format = {})

        self.triggered = triggered
        
        self.params['estimated_readout_lag'] = 1257 # microseconds
        self.params['frameTimeout'] = frameTimeout
        self.params['triggerType'] = triggerType
        
        ReleaseDriver()
        LoadDriver()
        
        cam = OpenCamera(ListCameras()[cam_id])
        
        self.set_cam_settings(cam)
        
        cam.StartStreaming()
        frame = cam.GrabFrame()
        self.dtype = np.uint16
        buf = np.frombuffer(frame.stringBuffer,
                            dtype = self.dtype).reshape(
                                (frame.width,frame.height))
        self.h = buf.shape[1]
        self.w = buf.shape[0]
        self._init_variables(dtype = self.dtype)
        cam.StopStreaming()
        
        cam.CloseCamera()
        ReleaseDriver()
        
        display("Got info from camera (name: {0})".format(cam_id))
    
    def set_cam_settings(self, cam, triggerType = 0):
        cam.settings.readoutSpeed=0 # 0=20MHz, 1=10MHz, 7=40MHz
        cam.settings.imageFormat = 'mono16'
        cam.settings.binning = self.binning
        cam.settings.emGain = self.gain
        cam.settings.triggerType = triggerType
        cam.settings.exposure = self.exposure - self.estimated_readout_lag
        cam.settings.blackoutMode=True
        cam.settings.Flush()
    
    def wait_for_start_trigger(self):
        while not self.start_trigger.is_set():
            # limits resolution to 1 ms 
            time.sleep(0.001)
            if self.close_event.is_set():
                return
        
    def run(self):
        #buf = np.frombuffer(self.frame.get_obj(),
        #                    dtype = self.dtype).reshape([
        #                        self.w,self.h,self.nchan])
        ReleaseDriver()
        self.close_event.clear()
        while not self.close_event.is_set():
            self.nframes.value = 0
            LoadDriver()
            if not self.camera_ready.is_set():
                # prepare camera
                cam = OpenCamera(ListCameras()[self.cam_id])
                if cam.settings.coolerActive:
                    display('QImaging - cooler active.')
                triggerType = self.triggerType if self.triggered.is_set() else 0
                self.set_cam_settings(cam, triggerType = self.triggerType)
                
                display('QImaging - Camera ready!')
                self.camera_ready.set()
                self.nframes.value = 0
            self.wait_for_start_trigger()
            queue = CameraQueue(cam)
            queue.start()
            display('QImaging - Started acquisition.')
            self.camera_ready.clear()
            while not self.stop_trigger.is_set():
                # run and acquire frames
                try:
                    f = queue.get(True, 1)
                except queue.Empty:
                    continue
                self.nframes.value += 1
                frame = np.ndarray(buffer = f.stringBuffer,
                                   dtype = self.dtype,
                                   shape = (self.w,
                                            self.h)).copy()
                timestamp = f.timeStamp
                frameID = f.frameNumber
                if self.saving.is_set():
                    self.was_saving = True
                    self.queue.put((frame.reshape([self.h,self.w]),
                                    (frameID,timestamp)))
                elif self.was_saving:
                    self.was_saving = False
                    self.queue.put(['STOP'])
                self.img[:] = np.reshape(frame,self.img.shape)[:]

                queue.put(f)
            queue.stop()
            cam.settings.blackoutMode=False
            cam.settings.Flush()
            cam.Abort()
            cam.CloseCamera()
            self.saving.clear()
            self.start_trigger.clear()
            self.stop_trigger.clear()
            ReleaseDriver()
            time.sleep(0.01)
            display('QImaging - Stopped acquisition.')
