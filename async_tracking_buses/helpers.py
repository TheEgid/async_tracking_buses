import logging
from dataclasses import dataclass
import configparser
import aiofiles
import os


BUSES = {}
windows_bounds = None

conn_attempt = 0
broadcast_logger = None
server_logger = None


@dataclass
class WindowBounds:
    south_lat: float
    north_lat: float
    west_lng: float
    east_lng: float

    def is_inside(self, lat, lng):
        is_inside_lat = self.south_lat < lat < self.north_lat
        is_inside_lng = self.west_lng < lng < self.east_lng
        return all([is_inside_lat, is_inside_lng])

    def update(self, south_lat, north_lat, west_lng, east_lng):
        pass


@dataclass
class Bus:
    busId: str
    lat: float
    lng: float
    route: str


def install_logs_parameters(logs=False):
    level = logging.CRITICAL
    if logs:
        level = logging.INFO
    str_format = '%(asctime)s\t %(filename)s %(message)s'
    date_format = '%d-%b-%y %H:%M:%S'
    logging.basicConfig(format=str_format, datefmt=date_format, level=level)
    broadcast_logger = logging.getLogger()
    return broadcast_logger


def load_settings():
    config = configparser.ConfigParser()
    config.read('settings.ini')
    return config['main_settings']


async def load_log_from_file(log_path, log_filename='history.txt'):
    log_file = os.path.join(log_path, log_filename)
    log = []
    if os.path.exists(log_file):
        async with aiofiles.open(log_file, encoding="utf-8") as f:
            async for data in f:
                log.append(data)
    return log
