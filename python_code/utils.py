from __future__ import print_function
import cv2
import sys
import os
from functools import partial
from datetime import datetime
from glob import glob
import os
import sys
import json
from os.path import join as pjoin
from scipy.interpolate import interp1d
from tqdm import tqdm
import numpy as np
import time
import pandas as pd

tstart = [time.time()]


def display(msg):
    try:
        sys.stdout.write('['+datetime.today().strftime('%y-%m-%d %H:%M:%S')+'] - ' + msg + '\n')
        sys.stdout.flush()
    except:
        pass


preferencepath = pjoin(os.path.expanduser('~'), 'labcams')

# This has the cameras and properties
_RECORDER_SETTINGS = {'recorder':['tiff','ffmpeg','binary'],
                      'recorder_help':'Different recorders allow saving data in different formats or using compresssion. Note that the realtime compression enabled by the ffmpeg video recorder can require specific hardware.',
                      'recording_queue':True,
                      'recording_queue_help':'Whether to use an intermediate queue for copying data from the camera, can assure that all data are stored regardless of disk usage; do not use this when recording at very high rates (1kHz) because it may introduce an overhead)'}

_SERVER_SETTINGS = {'server':['udp','zmq','none'],
                    'server_help':'These option allow setting servers to enable controlling the cameras and adding information to the log during recording. ',
                    'server_refresh_time':30,
                    'server_refresh_time_help':'How often to listen to messages (in ms)',
                    'server_port':9999}

_OTHER_SETTINGS = dict(recorder_path = 'I:\\data',
                       recorder_frames_per_file = 0,
                       recorder_frames_per_file_help = 'number of frames per file (0 is for a single large file)',
                       recorder_sleep_time = 0.03,
                       recorder_path_format = pjoin('{datafolder}',
                                                    '{dataname}',
                                                    '{filename}',
                                                    '{today}_{run}_{nfiles}'))

_CAMERAS = dict(avt='Allied Vision Technology (AVT Mako,Manta... - pymba/Vimba)',
                qimaging = 'QImaging (EMC2 - Legacy driver)',
                opencv = 'OpenCV camera (Webcam, ...)',
                pco = 'PCO imaging - PCO Edge (PCO SDK)',
                ximea = 'Ximea (python sdk)',
                pointgrey = 'FLIR PointGrey - Chameleon 3 (PySpin/FLIR Spinnaker SDK)')
# description and id are mandatory
_CAMERA_SETTINGS = dict(avt = dict(name='camera serial number',
                                   TriggerSource = 'Line1',
                                   TriggerMode = 'LevelHigh',
                                   TriggerSelector = 'FrameStart',
                                   AcquisitionMode = 'Continuous',
                                   AcquisitionFrameCount=1000,
                                   nFrameBuffers=6,
                                   gain = 0,
                                   frameRate=60.),
                        qimaging=dict(exposure=100,
                                      gain=3600,
                                      binning = 4,
                                      triggerType = 0),
                        opencv = dict(id = 0,
                                      frameRate = 0),
                        pco = dict(id = 0,
                                   exposure=33),
                        ximea = dict(id = 0,
                                     exposure=33,
                                     binning = 4),
                        pointgrey = dict(roi = 'full sensor of [X,Y,W,H]',
                                         pxformat='Mono8',
                                         serial='Camera serial number',
                                         binning = 1,
                                         exposure = 7000,
                                         gamma = 1.0,
                                         hardware_trigger = 'out_line3',
                                         frameRate = 100.))


DEFAULTS = dict(cams = [{'description':'facecam',
                         'name':'Mako G-030B',
                         'driver':'AVT',
                         'gain':10,
                         'frameRate':31.,
                         'TriggerSource':'Line1',
                         'TriggerMode':'LevelHigh',
                         'NBackgroundFrames':1.,
                         'Save':True},
                        {'description':'1photon',
                         'name':'qcam',
                         'id':0,
                         'driver':'QImaging',
                         'gain':1500,
                         'triggerType':1,
                         'binning':2,
                         'exposure':100000,
                         'frameRate':0.1},
                        {'name':'webcam',
                         'driver':'OpenCV',
                         'description':'webcam',
                         'id':0},
                        {'description':'1photon',
                         'driver':'PCO',
                         'exposure':33,
                         'id':0,
                         'name':'pco.edge',
                         'triggerType':0,
                         'recorder':'binary'}],
                recorder_path = 'I:\\data',
                recorder_frames_per_file = 256,
                recorder_sleep_time = 0.05,
                server_port = 100000,
                compress = 0)


defaultPreferences = DEFAULTS


def getPreferences(preffile = None,create = True):
    ''' Reads the parameters from the home directory.

    pref = getPreferences(expname)

    User parameters like folder location, file preferences, paths...
    Joao Couto - May 2018
    '''
    prefpath = preferencepath
    if preffile is None:
        
        preffile = pjoin(preferencepath,'default.json')
    else:
        prefpath = os.path.dirname(preffile)
    if not os.path.isfile(preffile) and create:
        display('Creating preference file from defaults.')
        if not os.path.isdir(prefpath):
            os.makedirs(prefpath)
        with open(preffile, 'w') as outfile:
            json.dump(defaultPreferences, outfile, sort_keys = True, indent = 4)
            display('Saving default preferences to: ' + preffile)
            print('\t\t\t\t Edit the file before launching.')
            sys.exit(0)

    if os.path.isfile(preffile):
        with open(preffile, 'r') as infile:
            pref = json.load(infile)
        
    return pref


def chunk_indices(nframes, chunksize = 512, min_chunk_size = 16):
    '''
    Gets chunk indices for iterating over an array in evenly sized chunks
    Joao Couto - from wfield
    '''
    chunks = np.arange(0,nframes,chunksize,dtype = int)
    if (nframes - chunks[-1]) < min_chunk_size:
        chunks[-1] = nframes
    if not chunks[-1] == nframes:
        chunks = np.hstack([chunks,nframes])
    return [[chunks[i],chunks[i+1]] for i in range(len(chunks)-1)]


def cameraTimesFromVStimLog(logdata,plog,camidx = 3,nExcessFrames=10):
    '''
    Interpolate cameralog frames to those recorded by pyvstim
    '''
    campulses = plog['cam{0}'.format(camidx)]['value'].iloc[-1] 
    if not ((logdata['frame_id'].iloc[-1] > campulses - nExcessFrames) and
            (logdata['frame_id'].iloc[-1] < campulses + nExcessFrames)):
        print('''WARNING!!

Recorded camera frames {0} dont fit the log {1}. 

Check the log/cables.

Interpolating on the first and last frames.
'''.format(logdata['frame_id'].iloc[-1],campulses))
        logdata['duinotime'] = interp1d(
            plog['cam{0}'.format(camidx)]['value'].iloc[[0,-1]],
            plog['cam{0}'.format(camidx)]['duinotime'].iloc[0,-1],
            fill_value="extrapolate")(logdata['frame_id'])

    else:
        logdata['duinotime'] = interp1d(
            plog['cam{0}'.format(camidx)]['value'],
            plog['cam{0}'.format(camidx)]['duinotime'],
            fill_value="extrapolate")(logdata['frame_id'])
    return logdata


def unpackbits(x,num_bits = 16,output_binary = False):
    '''
    unpacks numbers in bits.
    '''
    if type(x) == pd.core.series.Series:
        x = np.array(x)
    
    xshape = list(x.shape)
    x = x.reshape([-1,1])
    to_and = 2**np.arange(num_bits).reshape([1,num_bits])
    bits = (x & to_and).astype(bool).astype(int).reshape(xshape + [num_bits])
    if output_binary:
        return bits.T
    mult = 1
    sync_idx_onset = np.where(mult*np.diff(bits,axis = 0)>0)
    sync_idx_offset = np.where(mult*np.diff(bits,axis = 0)<0)
    onsets = {}
    offsets = {}
    for ichan in np.unique(sync_idx_onset[1]):
        onsets[ichan] = sync_idx_onset[0][
            sync_idx_onset[1] == ichan]
    for ichan in np.unique(sync_idx_offset[1]):
        offsets[ichan] = sync_idx_offset[0][
            sync_idx_offset[1] == ichan]
    return onsets,offsets

################################################################################
################################################################################
################################################################################

def parseCamLog(fname, readTeensy = False):
    logheaderkey = '# Log header:'
    comments = []
    with open(fname,'r') as fd:
        for line in fd:
            if line.startswith('#'):
                line = line.strip('\n').strip('\r')
                comments.append(line)
                if line.startswith(logheaderkey):
                    columns = line.strip(logheaderkey).strip(' ').split(',')

    logdata = pd.read_csv(fname, 
                          delimiter=',',
                          header=None,
                          comment='#',
                          engine='c')
    col = [c for c in logdata.columns]
    for icol in range(len(col)):
        if icol <= len(columns)-1:
            col[icol] = columns[icol]
        else:
            col[icol] = 'var{0}'.format(icol)
    logdata.columns = col
    if readTeensy:
        # get the sync pulses and frames along with the LED
        def _convert(string):
            try:
                val = int(string)
            except ValueError as err:
                val = float(string)
            return val

        led = []
        sync= []
        ncomm = []
        for l in comments:
            if l.startswith('#LED:'):
                led.append([_convert(f) for f in  l.strip('#LED:').split(',')])
            elif l.startswith('#SYNC:'):
                sync.append([0.] + [_convert(f) for f in  l.strip('#SYNC:').split(',')])
            elif l.startswith('#SYNC1:'):
                sync.append([1.] + [_convert(f) for f in  l.strip('#SYNC1:').split(',')])
            else:
                ncomm.append(l)
        sync = pd.DataFrame(sync, columns=['sync','count','frame','timestamp'])
        led = pd.DataFrame(led, columns=['led','frame','timestamp'])
        return logdata,led,sync,ncomm
    return logdata,comments

parse_cam_log = parseCamLog

class TiffStack(object):
    def __init__(self,filenames):
        if type(filenames) is str:
            filenames = np.sort(glob(pjoin(filenames,'*.tif')))
        
        assert type(filenames) in [list,np.ndarray], 'Pass a list of filenames.'
        self.filenames = filenames
        for f in filenames:
            assert os.path.exists(f), f + ' not found.'
        # Get an estimate by opening only the first and last files
        framesPerFile = []
        self.files = []
        for i,fn in enumerate(self.filenames):
            if i == 0 or i == len(self.filenames)-1:
                self.files.append(TiffFile(fn))
            else:
                self.files.append(None)                
            f = self.files[-1]
            if i == 0:
                dims = f.series[0].shape
                self.shape = dims
            elif i == len(self.filenames)-1:
                dims = f.series[0].shape
            framesPerFile.append(np.int64(dims[0]))
        self.framesPerFile = np.array(framesPerFile, dtype=np.int64)
        self.framesOffset = np.hstack([0,np.cumsum(self.framesPerFile[:-1])])
        self.nFrames = np.sum(framesPerFile)
        self.curfile = 0
        self.curstack = self.files[self.curfile].asarray()
        N,self.h,self.w = self.curstack.shape[:3]
        self.dtype = self.curstack.dtype
        self.shape = (self.nFrames,self.shape[1],self.shape[2])
    def getFrameIndex(self,frame):
        '''Computes the frame index from multipage tiff files.'''
        fileidx = np.where(self.framesOffset <= frame)[0][-1]
        return fileidx,frame - self.framesOffset[fileidx]
    def __getitem__(self,*args):
        index  = args[0]
        if not type(index) is int:
            Z, X, Y = index
            if type(Z) is slice:
                index = range(Z.start, Z.stop, Z.step)
            else:
                index = Z
        else:
            index = [index]
        img = np.empty((len(index),self.h,self.w),dtype = self.dtype)
        for i,ind in enumerate(index):
            img[i,:,:] = self.getFrame(ind)
        return np.squeeze(img)
    def getFrame(self,frame):
        ''' Returns a single frame from the stack '''
        fileidx,frameidx = self.getFrameIndex(frame)
        if not fileidx == self.curfile:
            if self.files[fileidx] is None:
                self.files[fileidx] = TiffFile(self.filenames[fileidx])
            self.curstack = self.files[fileidx].asarray()
            self.curfile = fileidx
        return self.curstack[frameidx,:,:]
    def __len__(self):
        return self.nFrames

def mmap_dat(filename,
             mode = 'r',
             nframes = None,
             shape = None,
             dtype='uint16'):
    '''
    Loads frames from a binary file as a memory map.
    This is useful when the data does not fit to memory.
    
    Inputs:
        filename (str)       : fileformat convention, file ends in _NCHANNELS_H_W_DTYPE.dat
        mode (str)           : memory map access mode (default 'r')
                'r'   | Open existing file for reading only.
                'r+'  | Open existing file for reading and writing.                 
        nframes (int)        : number of frames to read (default is None: the entire file)
        shape (list|tuple)   : dimensions (NCHANNELS, HEIGHT, WIDTH) default is None
        dtype (str)          : datatype (default uint16) 
    Returns:
        A memory mapped  array with size (NFRAMES,[NCHANNELS,] HEIGHT, WIDTH).

    Example:
        dat = mmap_dat(filename)

    Joao Couto - from wfield
    '''
    
    if not os.path.isfile(filename):
        raise OSError('File {0} not found.'.format(filename))
    if shape is None or dtype is None: # try to get it from the filename
        meta = os.path.splitext(filename)[0].split('_')
        if shape is None:
            try: # Check if there are multiple channels
                shape = [int(m) for m in meta[-4:-1]]
            except ValueError:
                shape = [int(m) for m in meta[-3:-1]]
        if dtype is None:
            dtype = meta[-1]
    dt = np.dtype(dtype)
    if nframes is None:
        # Get the number of samples from the file size
        nframes = int(os.path.getsize(filename)/(np.prod(shape)*dt.itemsize))
    dt = np.dtype(dtype)
    return np.memmap(filename,
                     mode=mode,
                     dtype=dt,
                     shape = (int(nframes),*shape))


def stack_to_mj2_lossless(stack,fname, rate = 30):
    '''
    Compresses a uint16 stack with FFMPEG and libopenjpeg
    
    Inputs:
        stack                : array or memorymapped binary file
        fname                : output filename (will change extension to .mov)
        rate                 : rate of the mj2 movie [30 Hz default]

    Example:
       from labcams.io import * 
       fname = '20200710_140729_2_540_640_uint16.dat'
       stack = mmap_dat(fname)
       stack_to_mj2_lossless(stack,fname, rate = 30)
    '''
    ext = os.path.splitext(fname)[1]
    assert len(ext), "[mj2 conversion] Need to pass a filename {0}.".format(fname)
    
    if not ext == '.mov':
        print('[mj2 conversion] Changing extension to .mov')
        outfname = fname.replace(ext,'.mov')
    else:
        outfname = fname
    assert stack.dtype == np.uint16, "[mj2 conversion] This only works for uint16 for now."

    nstack = stack.reshape([-1,*stack.shape[2:]]) # flatten if needed    
    sq = FFmpegWriter(outfname, inputdict={'-pix_fmt':'gray16le',
                                              '-r':str(rate)}, # this is important
                      outputdict={'-c:v':'libopenjpeg',
                                  '-pix_fmt':'gray16le',
                                  '-r':str(rate)})
    from tqdm import tqdm
    for i,f in tqdm(enumerate(nstack),total=len(nstack)):
        sq.writeFrame(f)
    sq.close()
    
