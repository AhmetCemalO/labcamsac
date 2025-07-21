#!/usr/bin/env python
# Install script for labcams.
# Joao Couto - March 2017
import os
from os.path import join as pjoin
from setuptools import setup, find_packages
from setuptools.command.install import install

with open("readme-pip.md", "r") as fh:
    longdescription = fh.read()

setup(
    name = 'neucams',
    version = '1.0',
    author = 'neucams',
    author_email = '',
    description = 'neucams: multi-camera control and recording',
    long_description = longdescription,
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/AhmetCemalO/neucams',
    license = 'GPL',
    packages = ['neucams'],
    python_requires = '>=3.7',
    install_requires = [
        'PyYAML==6.0.2',
        'genicam==1.4.0',
        'harvesters==1.4.3',
        'opencv-python==4.5.1.48',
        'pco==0.1.3',
        'pymba==0.3.7',
        'scikit-video==1.1.11',
        'vmbpy==1.0.5',
        'natsort',
        'numpy',
        'olefile',
        'pandas',
        'Pillow',
        'pyqt5',
        'pyqt5-sip',
        'pyqtchart',
        'pyqtgraph',
        'pyqtwebengine',
        'pyserial',
        'python-dateutil',
        'pytz',
        'pyzmq',
        'scipy',
        'six',
        'tifffile',
        'tqdm',
        'wincertstore',
    ],
    entry_points = {
        'console_scripts': [
            'neucams = __main__:main',
        ]
    },
)


