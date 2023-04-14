import logging
import os
from pathlib import Path
from zipfile import ZipFile
from logging.handlers import TimedRotatingFileHandler

logger_needs_setup = True


def namer(name):
    return name + ".zip"


def rotator(source, dest):
    with open(source, "r") as sf:
        data = sf.read()
        with ZipFile(dest, "w") as zipf:
            zipf.writestr(Path(source).name, data)
    os.remove(source)


def setup_logger(filename: str):
    """Run to setup analogue of loguru logger used in original app"""
    global logger_needs_setup
    if logger_needs_setup:
        logger_needs_setup = False
        f_handler = TimedRotatingFileHandler(filename, when='D', interval=1)
        f_handler.setLevel(logging.DEBUG)
        f_handler.rotator = rotator
        f_handler.namer = namer
        f_format = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        f_handler.setFormatter(f_format)
        logger.addHandler(f_handler)


logger = logging.getLogger('upstream-viz-lib')

