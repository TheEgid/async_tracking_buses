import json
import logging
from dataclasses import dataclass

import jsonschema

BUSES = {}
BUSES_COUNTER = set()

conn_attempt = 0
broadcast_logger = None
server_logger = None
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



def install_logs_parameters(logs=False):
    level = logging.CRITICAL
    if logs:
        level = logging.INFO
    str_format = '%(asctime)s\t %(filename)s %(message)s'
    date_format = '%d-%b-%y %H:%M:%S'
    logging.basicConfig(format=str_format, datefmt=date_format, level=level)
    broadcast_logger = logging.getLogger()
    return broadcast_logger


def validate_input_json_data(json_data):
    with open('bounds_schema.json', 'r') as f:
        schema_data = f.read()
        json_schema = json.loads(schema_data)
    try:
        jsonschema.validate(json_data, json_schema)
    except jsonschema.exceptions.ValidationError:
        return None
    return json_data
