import unittest
import sys
import os
from os.path import isfile, join, dirname, abspath
import shutil
import time
test_path = dirname(abspath(__file__))
code_path = dirname(test_path)
sys.path.append(code_path)

from camera_handler import CameraHandler

class TestCameraHandler(unittest.TestCase):
    def get_cam_dict(self):
        cam_dict = {'description':'facecam',
                    'name':'Mako G-030B',
                    'driver':'avt',
                    'params': {'gain':10,
                               'frameRate':31.,
                               'TriggerSource':'Line1',
                               'TriggerMode':'LevelHigh',
                               'NBackgroundFrames':1.}}
        return cam_dict

    def get_writer_dict(self):
        writer_dict = {'writer': 'opencv',
                       'filename': 'autogen_test_record', #without extension
                       'dataname': 'autogen_test_camera_handler',
                       'datafolder': test_path,
                       'pathformat': join('{datafolder}','{dataname}','{filename}','{run}_{nfiles}'),
                       'frames_per_file': 0}
        return writer_dict
        
    def test_camera_handler(self):
        cam_dict = self.get_cam_dict()
        writer_dict = self.get_writer_dict()
        self.camera_handler = CameraHandler(cam_dict, writer_dict)
        
        time.sleep(0.1)
        assert not self.camera_handler.camera_ready.is_set()
        assert not self.camera_handler.is_running.is_set()
        assert not self.camera_handler.start_trigger.is_set()
        assert not self.camera_handler.stop_trigger.is_set()
        assert not self.camera_handler.saving.is_set()
        assert not self.camera_handler.close_event.is_set()
        # assert self.camera_handler.img is None
        
        self.camera_handler.start()
        
        while not self.camera_handler.camera_ready.is_set():
            time.sleep(0.1)
            
        assert self.camera_handler.camera_ready.is_set()
        assert not self.camera_handler.is_running.is_set()
        assert not self.camera_handler.start_trigger.is_set()
        assert not self.camera_handler.stop_trigger.is_set()
        assert not self.camera_handler.saving.is_set()
        assert not self.camera_handler.close_event.is_set()
        # assert self.camera_handler.img is not None
        
        ret = self.camera_handler.start_acquisition()
        
        assert ret
        
        self.camera_handler.start_saving()
        
        time.sleep(0.1)
        assert not self.camera_handler.camera_ready.is_set()
        assert self.camera_handler.is_running.is_set()
        assert self.camera_handler.start_trigger.is_set()
        assert not self.camera_handler.stop_trigger.is_set()
        assert self.camera_handler.saving.is_set()
        assert not self.camera_handler.close_event.is_set()
        # assert self.camera_handler.img is not None
        
        time.sleep(0.5)
        self.camera_handler.stop_acquisition()
        
        time.sleep(0.1)
        self.camera_handler.close()
        
        self.camera_handler.join()

        try: # CLEAN
            dir_path = join(writer_dict['datafolder'], writer_dict['dataname'])
            shutil.rmtree(dir_path)
        except OSError as e:
            print("Error: %s : %s" % (dir_path, e.strerror))

if __name__ == '__main__':
    unittest.main()