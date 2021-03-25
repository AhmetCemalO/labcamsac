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
    sys.stdout.write('['+datetime.today().strftime('%y-%m-%d %H:%M:%S')+'] - ' + msg + '\n')
    sys.stdout.flush()

preferencepath = pjoin(os.path.expanduser('~'), 'labcams')

_RECORDER_SETTINGS = {'recorder':['tiff','ffmpeg','binary'],
                      'recorder_help':'Different recorders allow saving data in different formats or using compresssion. Note that the realtime compression enabled by the ffmpeg video recorder can require specific hardware.'}

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
                                                    
DEFAULTS = dict(cams = [{'description':'facecam',
                         'name':'Mako G-030B',
                         'driver':'AVT',
                         'gain':10,
                         'frameRate':31.,
                         'TriggerSource':'Line1',
                         'TriggerMode':'LevelHigh',
                         'NBackgroundFrames':1.},
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
        print('\t\t\t\t Edit the file before launching.', flush=True)
        sys.exit(0)

    if os.path.isfile(preffile):
        with open(preffile, 'r') as infile:
            pref = json.load(infile)
        
    return pref
