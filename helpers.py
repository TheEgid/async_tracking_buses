import logging
import os
import platform
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


def install_logs_parameters(logs=False):
    global broadcast_logger
    str_format = '%(asctime)s\t %(filename)s %(message)s'
    date_format = '%d-%b-%y %H:%M:%S'
    logging.basicConfig(format=str_format, datefmt=date_format,level=logging.INFO)
    broadcast_logger = logging.getLogger()
    return broadcast_logger
