import logging
import os
import platform
import webbrowser
from dataclasses import dataclass

BUSES = {}
BUSES_COUNTER = set()

conn_attempt = 0
broadcast_logger = None
_args = None

# x1, y1, x2, y2, x, y = [int(input()) for i in range(6)]
# if x2 >= x >= x1 and y2 <= y <= y1:
#     print('Точка принадлежит прямоугольнику')
# else:
#     print('Точка не принадлежит прямоугольнику')

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
    level = logging.CRITICAL
    if logs:
        level = logging.INFO
    str_format = '%(asctime)s\t %(filename)s %(message)s'
    date_format = '%d-%b-%y %H:%M:%S'
    logging.basicConfig(format=str_format, datefmt=date_format, level=level)
    broadcast_logger = logging.getLogger()
    return broadcast_logger
