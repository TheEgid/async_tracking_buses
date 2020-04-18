from dataclasses import dataclass
import os
import json
import logging
import time


BUSES = {}
windows_bounds = None
conn_attempt = 0


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


class BusesOnBoundsFilter(logging.Filter):
    def filter(self, record):
        frequency = 5
        time_local = time.localtime(record.created).tm_sec
        return time_local % frequency == 0



def get_json_schema(filepath):
    """Receipt JSON Schema object
        Args:
            filepath (str): JSON schema filepath made with
            https://jsonschema.net Web application that generates JSON schema.
        Returns:
            Deserialized JSON object
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f'{filepath} not found')
    with open(filepath, 'r') as f:
        schema = f.read()
        return json.loads(schema)
