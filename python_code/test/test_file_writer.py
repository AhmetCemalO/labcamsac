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

    def test_opencv_writer(self):
        """Write 60 frames of identical Lenna image into an avi file using the OpenCVWriter,
        read the generated video and count the frames, then delete created folders/file"""
        img = get_test_img()
        data_folder = test_path
        data_name = 'autogen_test_opencv_writer'
        filename = 'autogen_opencv_video' #without extension
        pathformat = join('{datafolder}','{dataname}','{filename}','{run}_{nfiles}')
        nfiles = 60
        # WRITE
        with OpenCVWriter(filename = filename, dataname = data_name,
                          datafolder = data_folder, pathformat = pathformat,
                          frames_per_file = 0, fourcc = 'XVID', frame_rate = 60) as writer:
            for i in range(nfiles):
                frame_id = i
                timestamp = time.time()
                metadata = (frame_id, timestamp) #dummy metadata but respect format
                writer.save(img, metadata)
        
        # READ
        path_dict = {'datafolder': data_folder, 'dataname': data_name, 'filename': filename, 'run': 'run000', 'nfiles': '{0:08d}'.format(0)}
        video_path = pathformat.format(**path_dict) + '.avi'
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
        assert i == nfiles
        
        # CLEAN
        try:
            dir_path = join(data_folder, data_name)
            shutil.rmtree(dir_path)
        except OSError as e:
            print("Error: %s : %s" % (dir_path, e.strerror))

if __name__ == '__main__':
    unittest.main()