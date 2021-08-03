import unittest
import sys
import os
import time
from os.path import isfile, join, dirname, abspath
import cv2

test_path = dirname(abspath(__file__))
code_path = dirname(test_path)
sys.path.append(code_path)

from cams.genicam import GenICam, GenI_get_cam_ids, get_gentl_producer_path

from harvesters.core import Harvester

class TestGenICam(unittest.TestCase):
    def get_ids(self):
        cam_ids, cam_infos = GenI_get_cam_ids()
        if len(cam_ids) > 0:
            print(cam_infos, flush=True)
        return cam_ids

    def test_manufacturer_access_cams(self):
        """If this fails it probably means that the camera IPv4 address is not detected by the Ethernet interface. Check the back of the Dalsa, if the LED is continuous blue it means it is correctly linked, if red or flashing blue it is not.
        You can fix this error(on Windows) by accessing Ethernet settings > Change adapter options > Ethernet > IPv4 > Properties and setting an IP address close to the one of the camera (which you can find in Vimba Viewer."""
        
        with Harvester() as h:
            h.add_file(get_gentl_producer_path())
            h.update()
            cams = h.device_info_list
            opened_cam = False
            if len(cams) > 0:
                with h.create_image_acquirer(0) as cam:
                    opened_cam = True
            self.assertTrue(opened_cam)
    
    def test_is_connected(self):
        cam = GenICam()
        self.assertTrue(cam.is_connected())
        cam.close()
        
    def test_access_cams(self):
        ids = self.get_ids()
        self.assertTrue(len(ids) > 0)
        for i in range(2):
            with GenICam(cam_id = ids[0]) as cam:
                img, _ = cam.image()
                self.assertTrue(img.shape[0] != 0)
                
    def test_get_features(self):
        ids = self.get_ids()
        self.assertTrue(len(ids) > 0)
        with GenICam(cam_id = ids[0]) as cam:
            self.assertTrue(cam.get_features() != "")

if __name__ == '__main__':
    unittest.main()