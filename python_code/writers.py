# Classes to save files from a multiprocessing queue
import time
import sys
from multiprocessing import Process,Queue,Event,Array,Value
from ctypes import c_long, c_char_p
from datetime import datetime
from .utils import display
import numpy as np
import os
from glob import glob
from os.path import join as pjoin
from tifffile import imread, TiffFile
from tifffile import TiffWriter as twriter
import pandas as pd
from skvideo.io import FFmpegWriter
import cv2

VERSION = 'B0.6'

class GenericWriter(object):
    def __init__(self,
                 filename = pjoin('dummy','run'),
                 dataname = 'eyecam',
                 pathformat = pjoin('{datafolder}','{dataname}','{filename}',
                                    '{today}_{run}_{nfiles}'),
                 datafolder=pjoin(os.path.expanduser('~'),'data'),
                 framesperfile=0,
                 incrementruns=True):
        if not hasattr(self,'extension'):
            self.extension = '.nan'
        self.saved_frame_count = 0
        self.runs = 0
        self.write = False
        self.close = False
        self.framesperfile = framesperfile
        self.filename = ''
        self.datafolder = datafolder
        self.dataname = dataname
        self.foldername = None
        self.incrementruns = incrementruns
        self.fd = None
        self.inQ = inQ
        self.parQ = None
        self.today = datetime.today().strftime('%Y%m%d')
        self.logfile = None
        self.nFiles = 0
        runname = 'run{0:03d}'.format(self.runs)
        self.path_format = pathformat
        self.path_keys =  dict(datafolder=self.datafolder,
                               dataname=self.dataname,
                               filename=self.filename,
                               today = self.today,
                               run = runname,
                               nfiles = '{0:08d}'.format(0),
                               extension = self.extension)
        if self.framesperfile > 0:
            if not '{nfiles}' in self.path_format:
                self.path_format += '_{nfiles}'

    def init(self,cam):
        ''' Sets camera specific variables - happens after camera load'''
        self.frame_rate = None
        if hasattr(cam,'frame_rate'):
            self.frame_rate = cam.frame_rate
        self.nchannels = 1
        if hasattr(cam,'nchan'):
            self.nchannels = cam.nchan

    def _stop_write(self):
        self.write = False
    def stop(self):
        self.write = False
    def set_filename(self,filename):
        self._stop_write()
        self.filename = filename
        display('Filename updated: ' + self.get_filename())

    def get_filename(self):
        return str(self.filename[:]).strip(' ')

    def get_filename_path(self):
        self.path_keys['run'] = 'run{0:03d}'.format(self.runs)
        nfiles = self.nFiles
        self.path_keys['nfiles'] = '{0:08d}'.format(nfiles)
        self.path_keys['filename'] = self.get_filename()
        filename = (self.path_format+'{extension}').format(**self.path_keys)
        folder = os.path.dirname(filename)
        if folder == '':
            filename = pjoin(os.path.abspath(os.path.curdir),filename)
            folder = os.path.dirname(filename)
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except Exception as e:
                print("Could not create folder {0}".format(folder))
                print(e)
        return filename

    def open_file(self, frame):
        filename = self.get_filename_path()
        if not self.fd is None:
            self.close_file()
        self._open_file(filename,frame)
        # Create a log file
        if self.logfile is None:
            self._open_logfile()
        self.nFiles += 1
        if hasattr(self,'parsed_filename'):
            filename = self.parsed_filename
        display('Opened: '+ filename)        
        self.logfile.write('# [' + datetime.today().strftime('%y-%m-%d %H:%M:%S')+'] - ' + filename + '\n')

    def _open_logfile(self):
        #self.path_keys['run'] = 'run{0:03d}'.format(self.runs)
        #nfiles = self.nFiles
        #self.path_keys['nfiles'] = '{0:08d}'.format(nfiles)
        #self.path_keys['filename'] = self.get_filename()

        #filename = (self.path_format+'{extension}').format(**self.path_keys)
        filename = self.get_filename_path()
        logfname = filename.replace('{extension}'.format(
            **self.path_keys),'.camlog')

        self.logfile = open(logfname,'w')
        self.logfile.write('# Camera: {0} log file'.format(
            self.dataname) + '\n')
        self.logfile.write('# Date: {0}'.format(
            datetime.today().strftime('%d-%m-%Y')) + '\n')
        self.logfile.write('# labcams version: {0}'.format(
            VERSION) + '\n')                
        self.logfile.write('# Log header:' + 'frame_id,timestamp' + '\n')

    def _open_file(self,filename,frame):
        pass

    def _write(self,frame,frameid,timestamp):
        pass

    def save(self,frame,metadata):
        return self._handle_frame((frame,metadata))
    
    def _handle_frame(self,buff):
        if buff[0] is None:
            # Then parameters were passed to the queue
            display('[Writer] - Received None...')
            return None,None
        if len(buff) == 1:
           # check message:
            msg = buff[0]
            if msg in ['STOP']:
                display('[Recorder] Stopping the recorder.')
                self._stop_write()
            elif msg.startswith('#'):
                if self.logfile is None:
                    self._open_logfile()
                self.logfile.write(msg + '\n')
            return None,msg
        else:
            frame,(metadata) = buff
            if (self.fd is None or
                (self.framesperfile > 0 and np.mod(self.saved_frame_count,
                                                   self.framesperfile)==0)):
                self.open_file(frame)
                if not self.inQ is None:
                    display('Queue size: {0}'.format(self.inQ.qsize()))

                    self.logfile.write('# [' + datetime.today().strftime('%y-%m-%d %H:%M:%S')+'] - '
                                       + 'Queue: {0}'.format(self.inQ.qsize())
                                       + '\n')
            frameid, timestamp = metadata[:2] 
            self._write(frame,frameid,timestamp)
            if np.mod(frameid,7000) == 0:
                if self.inQ is None:
                    display('[{0} - frame:{1}]'.format(
                        self.dataname,frameid))
                else:
                    display('[{0} - frame:{1}] Queue size: {2}'.format(
                        self.dataname,frameid,self.inQ.qsize()))
            self.logfile.write(','.join(['{0}'.format(a) for a in metadata]) + '\n')
            self.saved_frame_count += 1
        return frameid,frame
    
    def close_run(self):
        
        if not self.logfile is None:
            # Check if there are comments on the queue
            while not self.inQ.empty():
                buff = self.inQ.get()
                frameid,frame = self._handle_frame(buff)
            self.close_file()
            self.logfile.write('# [' +
                               datetime.today().strftime(
                                   '%y-%m-%d %H:%M:%S')+'] - ' +
                               "Wrote {0} frames on {1} ({2} files).".format(
                                   self.saved_frame_count,
                                   self.dataname,
                                   self.nFiles) + '\n')
            self.logfile.close()
            self.logfile = None
            display('[Recorder] Closing the logfile {0}.'.format(self.dataname))
            self.runs += 1
        if not self.saved_frame_count == 0:
            display("[Recorder] Wrote {0} frames on {1} ({2} files).".format(
                self.saved_frame_count,
                self.dataname,
                self.nFiles))

class GenericWriterProcess(Process,GenericWriter):
    def __init__(self,
                 inQ = None,
                 loggerQ = None,
                 filename = pjoin('dummy','run'),
                 dataname = 'eyecam',
                 pathformat = pjoin('{datafolder}','{dataname}','{filename}',
                                    '{today}_{run}_{nfiles}'),
                 datafolder=pjoin(os.path.expanduser('~'),'data'),
                 framesperfile=0,
                 sleeptime = 1./30,
                 incrementruns=True):
        GenericWriter.__init__(self,inQ = inQ,
                               loggerQ=loggerQ,
                               filename=filename,
                               datafolder=datafolder,
                               dataname=dataname,
                               pathformat=pathformat,
                               framesperfile=framesperfile,
                               incrementruns=incrementruns)
        Process.__init__(self)
        self.write = Event()
        self.close = Event()
        self.filename = Array('u',' ' * 1024)
        self.inQ = inQ
        self.parQ = Queue()
        self.daemon = True

    def _stop_write(self):
        self.write.clear()

    def set_filename(self,filename):
        self._stop_write()
        for i in range(len(self.filename)):
            self.filename[i] = ' '
        for i in range(len(filename)):
            self.filename[i] = filename[i]
        display('Filename updated: ' + self.get_filename())
    
    def stop(self):
        self._stop_write()
        self.close.set()
        self.join()
        
    def _write(self,frame,frameid,timestamp):
        pass
    
    def get_from_queue_and_save(self):
        buff = self.inQ.get()
        return self._handle_frame(buff)

    def run(self):
        while not self.close.is_set():
            self.saved_frame_count = 0
            self.nFiles = 0
            if not self.parQ.empty():
                self.getFromParQueue()
            while self.write.is_set() and not self.close.is_set():
                while self.inQ.qsize():
                    frameid,frame = self.get_from_queue_and_save()
                # spare the processor just in case...
                time.sleep(self.sleeptime)
            time.sleep(self.sleeptime)
            # If queue is not empty, empty if to disk.
            while self.inQ.qsize():
                frameid,frame = self.get_from_queue_and_save()
            #display('Queue is empty. Proceding with close.')
            # close the run
            self.close_run()
        
class TiffWriter(GenericWriterProcess):
    def __init__(self,
                 inQ = None,
                 loggerQ = None,
                 filename = pjoin('dummy','run'),
                 dataname = 'cam',
                 pathformat = pjoin('{datafolder}','{dataname}','{filename}',
                                    '{today}_{run}_{nfiles}'),
                 datafolder=pjoin(os.path.expanduser('~'),'data'),
                 framesperfile=256,
                 sleeptime = 1./30,
                 incrementruns=True,
                 compression=None):
        self.extension = '.tif'
        super(TiffWriter,self).__init__(inQ = inQ,
                                        loggerQ=loggerQ,
                                        datafolder=datafolder,
                                        filename=filename,
                                        dataname=dataname,
                                        pathformat=pathformat,
                                        framesperfile=framesperfile,
                                        sleeptime=sleeptime,
                                        incrementruns=incrementruns)
        self.compression = None
        if not compression is None:
            if compression > 9:
                display('Can not use compression over 9 for the TiffWriter')
            elif compression > 0:
                self.compression = compression
        self.tracker = None
        self.trackerfile = None
        self.trackerFlag = Event()
        self.trackerpar = None

    def close_file(self):
        if not self.fd is None:
            self.fd.close()
        self.fd = None

    def _open_file(self,filename,frame = None):
        self.fd = twriter(filename)

    def _write(self,frame,frameid,timestamp):
        self.fd.save(frame,
                     compress=self.compression,
                     description='id:{0};timestamp:{1}'.format(frameid,
                                                               timestamp))

################################################################################
################################################################################
################################################################################
class BinaryWriter(GenericWriterProcess):
    def __init__(self,
                 inQ = None,
                 loggerQ = None,
                 filename = pjoin('dummy','run'),
                 dataname = 'eyecam',
                 datafolder=pjoin(os.path.expanduser('~'),'data'),
                 pathformat = pjoin('{datafolder}','{dataname}','{filename}',
                                    '{today}_{run}_{nfiles}'),
                 framesperfile=0,
                 sleeptime = 1./300,
                 incrementruns=True):
        self.extension = '_{nchannels}_{H}_{W}_{dtype}.dat'
        super(BinaryWriter,self).__init__(inQ = inQ,
                                          loggerQ=loggerQ,
                                          filename=filename,
                                          datafolder=datafolder,
                                          dataname=dataname,
                                          pathformat = pathformat,
                                          framesperfile=framesperfile,
                                          sleeptime=sleeptime,
                                          incrementruns=incrementruns)
        self.w = None
        self.h = None
        self.buf = []

    def close_file(self):
        if not self.fd is None:
            self.fd.close()
        self.fd = None

    def _open_file(self,filename,frame = None):
        self.w = frame.shape[1]
        self.h = frame.shape[0]
        dtype = frame.dtype
        if dtype == np.float32:
            dtype='float32'
        elif dtype == np.uint8:
            dtype='uint8'
        else:
            dtype='uint16'
        filename = filename.format(nchannels = self.nchannels,
                                   W=self.w,
                                   H=self.h,
                                   dtype=dtype) 
        self.parsed_filename = filename
        self.fd = open(filename,'wb')
        
    def _write(self,frame,frameid,timestamp):
        self.fd.write(frame)
        if np.mod(frameid,5000) == 0: 
            display('Wrote frame id - {0}'.format(frameid))
        
################################################################################
################################################################################
################################################################################
class FFMPEGWriter(GenericWriterProcess):
    def __init__(self,
                 inQ = None,
                 loggerQ = None,
                 filename = pjoin('dummy','run'),
                 dataname = 'eyecam',
                 datafolder=pjoin(os.path.expanduser('~'),'data'),
                 pathformat = pjoin('{datafolder}','{dataname}','{filename}',
                                    '{today}_{run}_{nfiles}'),
                 framesperfile=0,
                 sleeptime = 1./30,
                 incrementruns=True,
                 hwaccel = None,
                 frame_rate = None,
                 compression=17):
        self.extension = '.avi'
        super(FFMPEGWriter,self).__init__(inQ = inQ,
                                          loggerQ=loggerQ,
                                          filename=filename,
                                          datafolder=datafolder,
                                          dataname=dataname,
                                          pathformat = pathformat,
                                          framesperfile=framesperfile,
                                          sleeptime=sleeptime,
                                          incrementruns=incrementruns)
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
        
    def close_file(self):
        if not self.fd is None:
            self.fd.close()
        self.fd = None

    def _open_file(self,filename,frame = None):
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
            self.fd = FFmpegWriter(filename.replace(self.extension,'.mov'),
                                   inputdict={'-pix_fmt':'gray16le',
                                              '-r':str(self.frame_rate)}, # this is important
                                   outputdict={'-c:v':'libopenjpeg',
                                               '-pix_fmt':'gray16le',
                                               '-r':str(self.frame_rate)})
        else:
            self.fd = FFmpegWriter(filename,
                                   inputdict=self.dinputs,
                                   outputdict=self.doutputs)
            
    def _write(self,frame,frameid,timestamp):
        self.fd.writeFrame(frame)

################################################################################
################################################################################
################################################################################
class OpenCVWriter(GenericWriter):
    def __init__(self,
                 inQ = None,
                 loggerQ = None,
                 filename = pjoin('dummy','run'),
                 dataname = 'eyecam',
                 pathformat = pjoin('{datafolder}','{dataname}','{filename}',
                                    '{today}_{run}_{nfiles}'),
                 datafolder=pjoin(os.path.expanduser('~'),'data'),
                 framesperfile=0,
                 sleeptime = 1./30,
                 incrementruns=True,
                 compression=None,
                 fourcc = 'X264'):
        self.extension = '.avi'
        super(OpenCVWriter,self).__init__(inQ = inQ,
                                          loggerQ=loggerQ,
                                          filename=filename,
                                          datafolder=datafolder,
                                          pathformat = pathformat,
                                          dataname=dataname,
                                          framesperfile=framesperfile,
                                          sleeptime=sleeptime,
                                          incrementruns=incrementruns)
        cv2.setNumThreads(6)
        self.compression = 17
        if not compression is None:
            if compression > 0:
                self.compression = compression
        self.fourcc = cv2.VideoWriter_fourcc(*fourcc)
        self.w = None
        self.h = None
        
    def close_file(self):
        if not self.fd is None:
            self.fd.release()
        self.fd = None

    def _open_file(self,filename,frame = None):
        self.w = frame.shape[1]
        self.h = frame.shape[0]
        self.isColor = False
        if len(frame.shape) < 2:
            self.isColor = True
        self.fd = cv2.VideoWriter(filename,
                                  cv2.CAP_FFMPEG,#cv2.CAP_DSHOW,#cv2.CAP_INTEL_MFX,
                                  self.fourcc,120,(self.w,self.h),self.isColor)

    def _write(self,frame,frameid,timestamp):
        if len(frame.shape) < 2:
            frame = cv2.cvtColor(frame,cv2.COLOR_GRAY2RGB)
        self.fd.write(frame)
