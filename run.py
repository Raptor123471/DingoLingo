import sys
import signal
import subprocess

print("You can close this window and the bot will run in background")
print("To stop the bot, press Ctrl+C")

if sys.platform == "win32":
    kwargs = {
        "creationflags": subprocess.CREATE_NO_WINDOW
        | subprocess.DETACHED_PROCESS
        | subprocess.CREATE_NEW_PROCESS_GROUP
    }
else:
    kwargs = {"start_new_session": True}
p = subprocess.Popen([sys.executable, "-m", "musicbot"], **kwargs)
try:
    p.wait()
except KeyboardInterrupt:
    p.send_signal(signal.SIGINT)
