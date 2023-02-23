"This file is here to automatically install the selected DB package"
import os
import sys
from pathlib import Path

# imitate running in root directory
cfg_dir = Path(__file__).parent
for i, path in enumerate(sys.path):
    if Path(path).absolute() == cfg_dir:
        sys.path[i] = str(cfg_dir.parent)

# inform that we're in installation phase
os.environ["DANDELION_INSTALLING"] = "1"

from setuptools import setup
from config.config import DATABASE_LIBRARY


setup(
    name="MusicBot DB",
    install_requires=[DATABASE_LIBRARY],
)
