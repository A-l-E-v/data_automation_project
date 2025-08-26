# В Теримнале 1: 
#   source .venv/bin/activate
#   python3 /home/al/data_automation_project/tools/run_debug_smtp.py
#
# В Терминале 2:
# python -m src.main --config config/config.yaml

import time
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Debugging

def run():
    controller = Controller(Debugging(), hostname="127.0.0.1", port=1025)
    controller.start()
    print("DEBUG SMTP server running on 127.0.0.1:1025 (prints received emails to console).")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping debug SMTP server...")
        controller.stop()

if __name__ == "__main__":
    run()
