import unittest
import sys
import os
from os.path import isfile, join, dirname, abspath
import cv2

test_path = dirname(abspath(__file__))
code_path = dirname(test_path)
sys.path.append(code_path)

from camera_handler import CameraHandler

class TestCameraHandler(unittest.TestCase):
    def get_cam_dict(self):
        pass
        # return cam_dict

    def get_writer_dict(self):
        pass
        
    def test_manufacturer_access_cams(self):
        """If this fails it probably means that the camera IPv4 address is not detected by the Ethernet interface.
        You can fix this error(on Windows) by accessing Ethernet settings > Change adapter options > Ethernet > IPv4 > Properties and setting an IP address close to the one of the camera (which you can find in Vimba Viewer."""
        with Vimba.get_instance() as vimba:
            cams = vimba.get_all_cameras()
            with cams[0] as cam:
                print(cam.get_id(), flush=True)

    def test_access_cams(self):
        ids = self.get_ids()
        for i in range(2):
            with AVTCam(cam_id = ids[0]) as cam:
                img, _ = cam.image()
                cv2.imshow('frame',img)
                cv2.waitKey(200)
                cv2.destroyAllWindows()
            

if __name__ == '__main__':
    unittest.main()