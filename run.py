"""
This file uses some magic to make running Dandelion
in the background easier
Head to musicbot/__main__.py if you want to see "real" main file
"""
import sys

if "--run" in sys.argv:
    import runpy

    runpy.run_module("musicbot", run_name="__main__")
    # reminder: there's no `exit` in frozen environment
    sys.exit()

import os
import signal
import subprocess

print("You can close this window and the bot will run in the background")
print("To stop the bot, press Ctrl+C")

on_windows = sys.platform == "win32"

if on_windows:
    import ctypes
    import ctypes.wintypes

    SetHandler = ctypes.windll.kernel32.SetConsoleCtrlHandler

    handler_type = ctypes.CFUNCTYPE(None, ctypes.wintypes.DWORD)
    SetHandler.argtypes = (handler_type, ctypes.c_bool)

    @handler_type
    def handler(event):
        if event == signal.CTRL_C_EVENT:
            os.kill(child_pid, signal.SIGTERM)

    kwargs = {
        "creationflags": subprocess.CREATE_NO_WINDOW
        | subprocess.CREATE_NEW_PROCESS_GROUP
    }
else:
    kwargs = {"start_new_session": True}

p = subprocess.Popen(
    # sys.executable may be python interpreter or pyinstaller exe
    [sys.executable, __file__, "--run"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    **kwargs,
)


# disable interrupting until we have the pid
# (we don't want to have a wild process at this point)
default_sigint_handler = signal.signal(signal.SIGINT, lambda s, f: None)

# the pid is passed via stdout because p.pid can be incorrect
line = p.stdout.readline()
try:
    child_pid = int(line)
except ValueError:
    print("Can't grab subprocess id, something is wrong!")
    print("The output is:", line, sep="\n", end="")
else:
    if on_windows:
        assert SetHandler(handler, True), "failed to set Ctrl+C handler"


def new_handler(sig, frame):
    """Handle the first interrupt and ignore others
    to prevent showing error instead of subprocess output"""
    global default_sigint_handler
    h = default_sigint_handler
    if h:
        default_sigint_handler = None
        h(sig, frame)


signal.signal(signal.SIGINT, new_handler)

try:
    while line := p.stdout.readline():
        print(line, end="")
except KeyboardInterrupt:
    if not on_windows:
        os.kill(child_pid, signal.SIGINT)
    print(p.stdout.read(), end="")

if p.wait() != 0:
    input("Press Enter to exit... ")
