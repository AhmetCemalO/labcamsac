import unittest
import sys
import os
import time
from os.path import isfile, join, dirname, abspath
import cv2

test_path = dirname(abspath(__file__))
code_path = dirname(test_path)
sys.path.append(code_path)

from cams.avt_cam import AVT_get_ids, AVTCam

from vimba import *

class TestAVTCam(unittest.TestCase):
    def get_ids(self):
        cam_ids, cam_infos = AVT_get_ids()
        if len(cam_ids) > 0:
            print(cam_ids, flush=True)
        return cam_ids

    # def test_manufacturer_access_cams(self):
        # """If this fails it probably means that the camera IPv4 address is not detected by the Ethernet interface.
        # You can fix this error(on Windows) by accessing Ethernet settings > Change adapter options > Ethernet > IPv4 > Properties and setting an IP address close to the one of the camera (which you can find in Vimba Viewer."""
        # with Vimba.get_instance() as vimba:
            # cams = vimba.get_all_cameras()
            # if len(cams) > 0:
                # with cams[0] as cam:
                    # print(cam.get_id(), flush=True)
            # else:
                # print("test_manufacturer_access_cams - NO AVT CAMERA CONNECTED, SKIP TEST")

    # def test_access_cams(self):
        # ids = self.get_ids()
        # if len(ids) > 0:
            # for i in range(2):
                # with AVTCam(cam_id = ids[0]) as cam:
                    # img, _ = cam.image()
                    # cv2.imshow('frame',img)
                    # cv2.waitKey(200)
                    # cv2.destroyAllWindows()
        # else:
            # print("test_access_cams - NO AVT CAMERA CONNECTED, SKIP TEST")
    
    def test_metadata(self):
        ids = self.get_ids()
        if len(ids) > 0:
            with AVTCam() as cam:
                t_start = time.time()
                while time.time() - t_start < 5:
                    img, metadata = cam.image()
                    print(metadata)
                    cv2.imshow('frame',img)
                    cv2.waitKey(10)
                cv2.destroyAllWindows()
        else:
            print("test_access_cams - NO AVT CAMERA CONNECTED, SKIP TEST")

if __name__ == '__main__':
    unittest.main()