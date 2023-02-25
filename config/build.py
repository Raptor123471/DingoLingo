import os
import sys
import glob
import runpy

from config.config import DATABASE_LIBRARY

sys.argv.extend(
    [
        "--onefile",
        # discord kindly provides us with opus dlls
        "--collect-binaries=discord",
        # make sure every file from musicbot folder is included
        *[
            "--hidden-import=" + os.path.splitext(file)[0].replace(os.path.sep, ".")
            for file in glob.glob("musicbot/**/*.py", recursive=True)
        ],
        "--hidden-import=" + DATABASE_LIBRARY,
        "-n=DandelionMusic",
        "-i=ui/note.ico",
        "run.py",
    ]
)

print("Running as:", *sys.argv)
runpy.run_module("PyInstaller", run_name="__main__")
