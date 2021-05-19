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

from tifffile import imread, TiffFile

def get_test_img():
    res_path = join(test_path,'res')
    lenna_path = join(res_path, 'Lenna_(test_image).png')
    return cv2.imread(lenna_path)

def get_complete_filepath(dir_path, filename):
    """the filepath we give to the writer will be modified with a suffix to avoid duplicates,
    so we have to find the new filepath"""
    complete_file_path = ""
    n_matching_files = 0
    for file in os.listdir(dir_path):
        if file.startswith(filename):
            complete_file_path = join(dir_path, file)
            n_matching_files += 1
    assert n_matching_files == 1
    assert isfile(complete_file_path)
    return complete_file_path
        
class TestFileWriter(unittest.TestCase):

    def setUp(self):
        self.img = get_test_img()
        self.generated_folders = []
        self.data_folder = test_path
        self.nframes = 60
    
    def tearDown(self):
        for folder in self.generated_folders:
            try:
                shutil.rmtree(folder)
            except OSError as e:
                print("Error: %s : %s" % (dir_path, e.strerror))

    def test_opencv_writer(self):
        """Write 60 frames of identical Lenna image into an avi file using the OpenCVWriter,
        read the generated video and count the frames, then delete created folders/file"""
        data_name = 'autogen_test_opencv_writer'
        filename = 'autogen_opencv_video' #without extension
        dir_path = join(self.data_folder, data_name)
        self.generated_folders.append(dir_path)
        filepath = join(dir_path, filename)
        # WRITE
        with OpenCVWriter(filepath = filepath) as writer:
            for i in range(self.nframes):
                frame_id = i
                timestamp = time.time()
                metadata = (frame_id, timestamp) #dummy metadata but respect format
                writer.save(self.img, metadata)
        # READ
        complete_file_path = get_complete_filepath(dir_path, filename)
        cap = cv2.VideoCapture(complete_file_path)
        assert cap.isOpened()
        i = 0
        while True:
            ret, frame = cap.read()
            if ret:
                i+=1
            else:
                break
        cap.release()
        assert i == self.nframes
        
    def test_tiff_writer(self):
        """Write 60 frames of identical Lenna image into a tiff file using the TiffWriter,
        read the generated images and count the frames, then delete created folders/file"""
        data_name = 'autogen_test_tiff_writer'
        filename = 'autogen_tiff_file' #without extension
        dir_path = join(self.data_folder, data_name)
        self.generated_folders.append(dir_path)
        filepath = join(dir_path, filename)
        # WRITE
        with TiffWriter(filepath = filepath) as writer:
            for i in range(self.nframes):
                frame_id = i
                timestamp = time.time()
                metadata = (frame_id, timestamp) #dummy metadata but respect format
                writer.save(self.img, metadata)
        # READ
        complete_file_path = get_complete_filepath(dir_path, filename)
        i = 0
        img_stack = imread(complete_file_path)
        with TiffFile(complete_file_path) as tif:
            for page in tif.pages:
                image = page.asarray()
                i+=1
        assert i == self.nframes

if __name__ == '__main__':
    unittest.main()