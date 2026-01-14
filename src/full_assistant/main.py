import gui
import logic

from gui import run_gui
from gui import _run_jarvis_safe
from gui import start_jarvis
from gui import process_log_queue


if __name__ == "__main__":
    run_gui()
    _run_jarvis_safe()
    start_jarvis()
    process_log_queue()

