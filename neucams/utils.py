import sys
from os import path, makedirs
from datetime import datetime
import json
import time
import platform
import subprocess
import logging

# Set up a basic logger
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

def display(s, level='info'):
    """
    Prints a string to the console, optionally with a datestring
    level: 'info' (default), 'warning', 'error'
    """
    log_func = getattr(logging, level, logging.info)
    log_func(s)

DEFAULT_SERVER_PARAMS = {
                         'server': 'udp',
                         'server_refresh_time':30, #ms
                         'server_port':9999
                         }
                      
DEFAULT_RECORDER_PARAMS = {
                            'recorder' : 'opencv',
                            'data_folder': 'C:\\Users\\User\\data',
                            'experiment_folder': 'EXP_TEST',
                            'frames_per_file': 256,
                            'compress': 0
                          }

DEFAULT_CAM_INFOS = [
                     {'description':'facecam',
                      'name':'Mako G-030B',
                      'driver':'avt',
                      'params': {'gain':10,
                                 'frameRate':31.,
                                 'TriggerSource':'Line1',
                                 'TriggerMode':'LevelHigh',
                                 'NBackgroundFrames':1.}},
                     {'description':'1photon',
                      'name':'qcam',
                      'id':0,
                      'driver':'QImaging',
                      'params': {'gain':1500,
                                 'triggerType':1,
                                 'binning':2,
                                 'exposure':100000,
                                 'frameRate':0.1}},
                     {'description':'webcam',
                      'name':'webcam',
                      'id':0,
                      'driver':'OpenCV'
                      },
                     {'description':'1photon-2',
                      'name':'pco.edge',
                      'id':0,
                      'driver':'pco',
                      'params': {'triggerType':0,
                                 'exposure':33},
                      'recorder_params': {'recorder' : 'binary'}}
                      ]

def get_default_folder():
    return path.join(path.expanduser('~'), 'labcams')

def get_default_preferences():
    return {'cams': DEFAULT_CAM_INFOS, 'recorder_params': DEFAULT_RECORDER_PARAMS, 'server_params' : DEFAULT_SERVER_PARAMS}
    
def write_template_to_file(filepath):
    display('Creating editable template.')
    dir_path = path.dirname(filepath)
    if not path.isdir(dir_path):
        makedirs(dir_path)
    with open(filepath, 'w') as outfile:
        json.dump(get_default_preferences(), outfile, sort_keys = True, indent = 4)
    display('Saved editable template to: ' + filepath)

def get_preferences(filepath = None, create_template = True):
    """
    
    """
    filepath = path.join(get_default_folder(),'default.json') if filepath is None else filepath
    pref = {}
    if path.isfile(filepath):
        try:
            with open(filepath, 'r') as infile:
                pref = json.load(infile)
            pref['user_config_path'] = filepath
            return True, pref
        except json.JSONDecodeError as e:
            error_msg = (f"JSON syntax error in file:\n{filepath}\nLine {e.lineno}, Column {e.colno}:\n{e.msg}")
            return error_msg, pref
        except Exception as e:
            return f"Error loading config file {filepath}: {e}", pref
        # Only run check_preferences if JSON loaded successfully
    else:
        if create_template:
            write_template_to_file(filepath)
        return False, pref

def check_preferences(pref, valid_drivers=None):
    error_messages = ""
    
    def check_missing_keys(dict, required_keys):
        missing_keys = []
        for key in required_keys:
            if not key in dict:
                missing_keys.append(key)
        return missing_keys
                
    cams = pref.get("cams", [])
    required_cam_keys = ['description', 'driver']
    descriptions = []
    for cam in cams:
        if "description" in cam:
            description =  cam["description"]
            if description in descriptions:
                error_messages += f"ERROR: descriptions have to be unique in your neucams config file at {pref.get('user_config_path', '')}. Those are used to determine the recorder subfolders.\n"
            descriptions.append(description)
        missing_keys = check_missing_keys(cam, required_cam_keys)
        if len(missing_keys) > 0:
            error_messages += f"ERROR: the following required keys are missing from your cam entry: {', '.join(missing_keys)}.\n"
        # Validate driver
        if valid_drivers is not None and 'driver' in cam:
            driver = cam['driver'].lower()
            if driver not in valid_drivers:
                error_messages += (
                    f"ERROR: Invalid driver '{driver}' in camera '{cam.get('description', '?')}'. "
                    f"Valid drivers are: {', '.join(valid_drivers)}.\n"
                )
    required_recorder_keys = ['data_folder', 'experiment_folder']
    if not "recorder_params" in pref:
        error_messages += f"ERROR: there needs to be a recorder_params entry, with at least the following required keys: {', '.join(required_recorder_keys)}.\n"
    else:
        missing_keys = check_missing_keys(pref["recorder_params"], required_recorder_keys)
        if len(missing_keys) > 0:
            error_messages += f"ERROR: the following required keys are missing from your recorder_params entry: {', '.join(missing_keys)}.\n"
    return error_messages

def resolve_cam_id_by_serial(driver, serial_number):
    """
    Given a driver and serial_number, return the correct cam_id for use with the camera class.
    """
    driver = driver.lower()
    if driver == 'genicam':
        # For GenICam, the serial number is used as the ID.
        return serial_number
    elif driver == 'pco':
        # PCO cameras are often opened by index, not ID.
        return None
    elif driver == 'avt':
        try:
            from vmbpy import VmbSystem
            with VmbSystem.get_instance() as vmb:
                for cam in vmb.get_all_cameras():
                    if hasattr(cam, 'get_serial') and cam.get_serial() == serial_number:
                        return cam.get_id()
            display(f"No AVT camera found with serial number {serial_number}", level='warning')
            return None # Not found
        except ImportError:
            display("vmbpy not found, cannot resolve AVT camera by serial.", level='error')
            return None
        except Exception as e:
            display(f"An error occurred while resolving AVT cam by serial: {e}", level='error')
            return None
    elif driver == "hamamatsu":
        try:
            # new API shipped with the `hamamatsu` / `pyDCAM` wheels
            # (they just ctypes-load dcamapi.dll, so the DLL-in-PATH trick you did still works)
            from hamamatsu.dcam import dcam           # or: from pydcam import dcam

            with dcam:                                # opens the DCAM runtime
                for idx, cam in enumerate(dcam):      # camera objects are iterable
                    if cam.info.get("serial_number") == serial_number:  # <-- replacement!
                        return idx                    # DCAM uses the index as camera-ID
        except Exception as exc:
            display(f"Hamamatsu lookup failed: {exc}", level="warning")

        return None
    else:
        display(f"Serial number resolution not implemented for driver: {driver}", level='warning')
        return None
    