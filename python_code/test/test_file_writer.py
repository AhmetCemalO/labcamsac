import unittest
import sys
import os
from os.path import isfile, join, dirname, abspath
import shutil
import re
import cv2
import numpy as np
import time

test_path = dirname(abspath(__file__))
code_path = dirname(test_path)
sys.path.append(code_path)

from file_writer import TiffWriter, BinaryWriter, FFMPEGWriter, OpenCVWriter

def get_test_img():
    res_path = join(test_path,'res')
    lenna_path = join(res_path, 'Lenna_(test_image).png')
    return cv2.imread(lenna_path)

class TestFileWriter(unittest.TestCase):

    def setUp(self):
        self.img = get_test_img()
        self.generated_folders = []
    
    def tearDown(self):
        for folder in self.generated_folders:
            try:
                shutil.rmtree(folder)
            except OSError as e:
                print("Error: %s : %s" % (dir_path, e.strerror))
            
    def test_opencv_writer(self):
        """Write 60 frames of identical Lenna image into an avi file using the OpenCVWriter,
        read the generated video and count the frames, then delete created folders/file"""
        data_folder = test_path
        data_name = 'autogen_test_opencv_writer'
        filename = 'autogen_opencv_video' #without extension
        dir_path = join(data_folder, data_name)
        self.generated_folders.append(dir_path)
        filepath = join(dir_path, filename)
        nframes = 60
        # WRITE
        with OpenCVWriter(filepath = filepath) as writer:
            for i in range(nframes):
                frame_id = i
                timestamp = time.time()
                metadata = (frame_id, timestamp) #dummy metadata but respect format
                writer.save(self.img, metadata)
        # READ
        video_path = ""
        for file in os.listdir(dir_path):
            if file.startswith(filename):
                video_path = join(dir_path, file)
                break
        print(video_path, flush=True)
        assert isfile(video_path)
        cap = cv2.VideoCapture(video_path)
        assert cap.isOpened()
        i = 0
        while True:
            ret, frame = cap.read()
            if ret:
                i+=1
                cv2.imshow('frame',frame)
            else:
                break
        cap.release()
        cv2.destroyAllWindows()
        assert i == nframes
        
        

if __name__ == '__main__':
    unittest.main()