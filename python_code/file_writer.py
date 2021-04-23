# Classes to save files from a multiprocessing queue
import time
import sys
import os
from os import path
from os.path import join as pjoin
from multiprocessing import Process,Queue,Event,Array,Value
import queue
from datetime import datetime
import numpy as np
from tifffile import imread, TiffFile, TiffWriter as twriter
from skvideo.io import FFmpegWriter
import cv2
from utils import display

VERSION = 'B0.6'

class RunWriter(Process):
    sleeptime = 0.05
    queue_timeout = 0.05
    
    def __init__(self, folder = 'dummy',
                       dataname = 'eyecam',
                       datafolder= pjoin(os.path.expanduser('~'),'data'),
                       pathformat = pjoin('{datafolder}','{dataname}','{folder}','{today}_{run}_{nfiles}'),
                       extension = 'log',
                       frames_per_file = 0):
        super().__init__()
        
        self.folder = folder
        self.folder_array = Array('u',' ' * 1024)
        
        self.path_format = pathformat
        today = datetime.today().strftime('%Y%m%d')
        self.path_dict = {'datafolder':datafolder,'dataname':dataname,'folder': folder, 'today': today, 'extension': extension}
        
        self.frames_per_file = frames_per_file

        self.close_flag = Event()
        self.stop_flag = Event()
        self.start_flag = Event()
        
        self.inQ = Queue()

        self.file_handler = None
        self.n_run = 0
        self.n_frames = 0
        self.n_files = 0
        
        self.start()
        self.start_flag.wait(2) #do not return handle before process started
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        self.join()
    
    def set_folder(self,folder):
        if self.start_flag.is_set():
            self.stop_flag.set()
        for i in range(len(self.folder_array)):
            self.folder_array[i] = ' '
        for i in range(len(folder)):
            self.folder_array[i] = folder[i]
        display('Folder updated: ' + self.get_folder_path())
        
    def get_folder_as_string(self):
        return str(self.folder_array[:]).strip(' ')
    
    def get_folder_path(self):
        return os.path.dirname(self.get_filepath())
        
    def get_filepath(self):
        self.path_dict['run'] = 'run{0:03d}'.format(self.n_run)
        self.path_dict['nfiles'] = '{0:08d}'.format(self.n_files)
        self.path_dict['folder'] = self.get_folder_as_string()
        filepath = (self.path_format + '.{extension}').format(**self.path_dict)
        return filepath

    def _init_file_handler(self, frame):
        """open file generic"""
        filepath = self.get_filepath()
        folder = os.path.dirname(filepath)
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except Exception as e:
                print(f"Could not create folder {folder} : {e}")
        self._release_file_handler()
        self.file_handler = self._get_file_handler(filepath,frame)
        self.n_files += 1
        
    def _get_file_handler(self, filepath, frame):
        """get specific file handler"""
        pass
        
    def _release_file_handler(self):
        """close specific file handler"""
        if self.file_handler is not None:
            self.file_handler.close()
            self.file_handler = None

    def _write(self,frame,frameid,timestamp):
        """write specific"""
        pass

    def save(self,frame,metadata):
        try:
            self.inQ.put((frame,metadata), timeout = self.queue_timeout)
        except queue.Full:
            print("ERROR: could not save image, queue is full")
    
    def run(self):
        self.set_folder(self.folder)
        self.start_flag.set()
        while not self.close_flag.is_set():
            self.saved_frame_count = 0
            self.n_files = 0
            while not self.stop_flag.is_set():
                time.sleep(self.sleeptime)
                self._process_queue()
            self._close_run()
    
    def _close_run(self):
        self._release_file_handler()
        self.n_run += 1
        if not self.saved_frame_count == 0:
            display("[Writer] Wrote {0} frames on {1} ({2} files).".format(self.saved_frame_count,
                                                                             self.path_dict['dataname'],
                                                                             self.n_files))
        self.stop_flag.clear()
  
    def _process_queue(self):
        while True:
            try:
                self._save_next_in_queue()
            except queue.Empty:
                break
            
    def _save_next_in_queue(self):
        buff = self.inQ.get(timeout = self.queue_timeout)
        self._handle_frame(buff)

    def _handle_frame(self, buff):
        # print(buff, flush=True)
        frame, metadata = buff
        if (self.file_handler is None or
            (self.frames_per_file > 0 and np.mod(self.saved_frame_count,
                                               self.frames_per_file)==0)):
            self._init_file_handler(frame)
        frameid, timestamp = metadata[:2] 
        self._write(frame,frameid,timestamp)
        self.saved_frame_count += 1
                
    def close(self):
        self.close_flag.set()
        self.stop_flag.set()
        
class TiffWriter(RunWriter):
    def __init__(self,
                 folder = pjoin('dummy','run'),
                 dataname = 'cam',
                 pathformat = pjoin('{datafolder}','{dataname}','{folder}',
                                    '{today}_{run}_{nfiles}'),
                 datafolder=pjoin(os.path.expanduser('~'),'data'),
                 frames_per_file=256,
                 compression=None):
        self.extension = '.tif'
        super().__init__(datafolder=datafolder,
                         folder=folder,
                         dataname=dataname,
                         pathformat=pathformat,
                         frames_per_file=frames_per_file)
        self.compression = None
        if not compression is None:
            if compression > 9:
                display('Can not use compression over 9 for the TiffWriter')
            elif compression > 0:
                self.compression = compression

    def _get_file_handler(self,filepath,frame = None):
        display('Opening: '+ filepath)
        return twriter(filepath)

    def _write(self,frame,frameid,timestamp):
        self.file_handler.save(frame,
                               compress=self.compression,
                               description='id:{0};timestamp:{1}'.format(frameid,timestamp))

class BinaryWriter(RunWriter):
    def __init__(self,folder = pjoin('dummy','run'),
                      dataname = 'eyecam',
                      datafolder=pjoin(os.path.expanduser('~'),'data'),
                      pathformat = pjoin('{datafolder}','{dataname}','{folder}',
                                    '{today}_{run}_{nfiles}'),
                      frames_per_file = 0,
                       **kwargs):
                      
        super().__init__(folder=folder,
                         datafolder=datafolder,
                         dataname=dataname,
                         pathformat = pathformat,
                         frames_per_file=frames_per_file,
                         extension = '_{n_chan}_{H}_{W}_{dtype}.dat')
        
    def _get_file_handler(self,filepath,frame = None):
        dtype = frame.dtype
        if dtype == np.float32:
            dtype='float32'
        elif dtype == np.uint8:
            dtype='uint8'
        else:
            dtype='uint16'
        filepath = filepath.format(n_chan = frame.shape[2],
                                        W = frame.shape[1],
                                        H = frame.shape[0],
                                    dtype = dtype)
        display('Opening: '+ filepath)
        return open(filepath,'wb')
        
    def _write(self,frame,frameid,timestamp):
        self.file_handler.write(frame)
        if np.mod(frameid,5000) == 0: 
            display('Wrote frame id - {0}'.format(frameid))
        
class FFMPEGWriter(RunWriter):
    def __init__(self, folder = pjoin('dummy','run'),
                       dataname = 'eyecam',
                       datafolder=pjoin(os.path.expanduser('~'),'data'),
                       pathformat = pjoin('{datafolder}','{dataname}','{folder}','{today}_{run}_{nfiles}'),
                       frames_per_file=0,
                       hwaccel = None,
                       frame_rate = None,
                       compression=17,
                       **kwargs):
                       
        super().__init__(folder = folder,
                         datafolder = datafolder,
                         dataname = dataname,
                         pathformat = pathformat,
                         frames_per_file = frames_per_file,
                         extension = '.avi')
                         
        self.compression = compression
        if frame_rate is None:
            frame_rate = 0
        if frame_rate <= 0:
            frame_rate = 30.
        self.frame_rate = frame_rate
        if hwaccel is None:
            self.doutputs = {'-format':'h264',
                             '-pix_fmt':'gray',
                             '-vcodec':'libx264',
                             '-threads':str(10),
                             '-crf':str(self.compression)}
        else:            
            if hwaccel == 'intel':
                if self.compression == 0:
                    display('Using compression 17 for the intel Media SDK encoder')
                    self.compression = 17
                self.doutputs = {'-format':'h264',
                                 '-pix_fmt':'yuv420p',#'gray',
                                 '-vcodec':'h264_qsv',#'libx264',
                                 '-global_quality':str(25), # specific to the qsv
                                 '-look_ahead':str(1),
                                 #preset='veryfast',#'ultrafast',
                                 '-threads':str(1),
                                 '-crf':str(self.compression)}
            elif hwaccel == 'nvidia':
                if self.compression == 0:
                    display('Using compression 25 for the NVIDIA encoder')
                    self.compression = 25
                self.doutputs = {'-vcodec':'h264_nvenc',
                                 '-pix_fmt':'yuv420p',
                                 '-cq:v':str(self.compression),
                                 '-threads':str(1),
                                 '-preset':'medium'}
        self.hwaccel = hwaccel
    
    def set_video_settings(self,cam):
        ''' Sets camera specific variables - happens after camera load'''
        self.frame_rate = None
        if hasattr(cam,'frame_rate'):
            self.frame_rate = cam.frame_rate
        self.nchannels = 1
        if hasattr(cam,'nchan'):
            self.nchannels = cam.nchan

    def _get_file_handler(self,filepath,frame = None):
        if frame is None:
            raise ValueError('[Recorder] Need to pass frame to open a file.')
        if self.frame_rate is None:
            self.frame_rate = 0
        if self.frame_rate == 0:
            display('Using 30Hz frame rate for ffmpeg')
            self.frame_rate = 30
        
        self.doutputs['-r'] =str(self.frame_rate)
        self.dinputs = {'-r':str(self.frame_rate)}
        
        # does a check for the datatype, if uint16 then save compressed lossless
        if frame.dtype in [np.uint16] and len(frame.shape) == 2:
            filepath = filepath.replace(self.extension,'.mov')
            inputdict={'-pix_fmt':'gray16le',
                      '-r':str(self.frame_rate)} # this is important
            outputdict={'-c:v':'libopenjpeg',
                       '-pix_fmt':'gray16le',
                       '-r':str(self.frame_rate)}
        else:
            inputdict=self.dinputs
            outputdict=self.doutputs
        display('Opening: '+ filepath)
        return FFmpegWriter(filepath, inputdict=inputdict, outputdict=outputdict)
            
    def _write(self,frame,frameid,timestamp):
        self.file_handler.writeFrame(frame)

class OpenCVWriter(RunWriter):
    def __init__(self, folder = pjoin('dummy','run'),
                       dataname = 'eyecam',
                       pathformat = pjoin('{datafolder}','{dataname}','{folder}','{today}_{run}_{nfiles}'),
                       datafolder = pjoin(os.path.expanduser('~'),'data'),
                       frames_per_file = 0,
                       fourcc = 'XVID', #'X264'
                       frame_rate = 60,
                       **kwargs):
        self.frame_rate = frame_rate
        cv2.setNumThreads(6)
        self.fourcc = cv2.VideoWriter_fourcc(*fourcc)
        self.w = None
        self.h = None
        super().__init__(folder = folder,
                         datafolder=datafolder,
                         pathformat = pathformat,
                         dataname=dataname,
                         extension = 'avi',
                         frames_per_file=frames_per_file)
        
    def _release_file_handler(self):
        if not self.file_handler is None:
            self.file_handler.release()
            self.file_handler = None

    def _get_file_handler(self,filepath,frame = None):
        self.w = frame.shape[1]
        self.h = frame.shape[0]
        self.isColor = False
        if len(frame.shape) < 2:
            self.isColor = True
        display('Opening: '+ filepath)
        return cv2.VideoWriter(filepath, self.fourcc, self.frame_rate,(self.w,self.h))
                                  
    def _write(self,frame,frameid,timestamp):
        if len(frame.shape) < 2 or frame.shape[2] == 1:
            frame = cv2.cvtColor(frame,cv2.COLOR_GRAY2RGB)
        self.file_handler.write(frame)
