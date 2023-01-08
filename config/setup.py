"This file is here to automatically install the selected DB package"
import os
import sys
from os.path import abspath, dirname

# imitate running in root directory
cfg_dir = dirname(__file__)
for i, path in enumerate(sys.path):
    if abspath(path) == cfg_dir:
        sys.path[i] = dirname(cfg_dir)

# inform that we're in installation phase
os.environ["DANDELION_INSTALLING"] = "1"

from setuptools import setup
from config.config import DATABASE


setup(
    name="MusicBot DB",
    install_requires=[DATABASE.partition("+")[2].partition(":")[0]],
)
