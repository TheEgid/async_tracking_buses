import logging
import os
import platform
import random
import time
import webbrowser
from dataclasses import dataclass

PAUSE_DUR = 1.5
BUSES = {}  # TODO rename
BUSES_COUNTER = set()


@dataclass
class Bus:
    busId: int
    lat: float
    lng: float
    route: str


def open_chrome_browser():
    os_name = platform.system()
    if os_name == 'Windows':
        chrome_path = r'"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" %s'
    elif os_name == 'Linux':
        chrome_path = r'"/usr/bin/google-chrome" %s'
    else:
        raise ValueError(f'unknown os: {os_name=}!')

    webbrowser.register('Chrome', None, webbrowser.BackgroundBrowser(chrome_path))
    link_path = os.path.join(os.getcwd(), 'index.html')
    webbrowser.get(chrome_path).open(link_path)


def generate_unical_hash(_lon=6):
    def has_letters(_):
        return any(symbol.isalpha() for symbol in _)
    offset = random.randint(100, 400)
    while has_letters('{0:010x}'.format(int(time.time() * offset))[:_lon]):
        return '{0:010x}'.format(int(time.time() * offset))[:_lon]
    else:
        return generate_unical_hash()


def install_logs_parameters(logs=False):
    global broadcast_logger
    str_format = '%(asctime)s\t %(filename)s %(message)s'
    date_format = '%d-%b-%y %H:%M:%S'
    logging.basicConfig(format=str_format, datefmt=date_format,level=logging.INFO)
    broadcast_logger = logging.getLogger()
    return broadcast_logger
