"This file is here to automatically install the selected DB package"
from setuptools import setup
from config import DATABASE


setup(
    name="MusicBot DB",
    install_requires=[DATABASE.partition("+")[2].partition(":")[0]],
)
