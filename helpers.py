import json
import logging
from dataclasses import dataclass
import jsonschema


BUSES = {}
WINDOWS_BOUNDS = {}

json_schema = None
conn_attempt = 0
broadcast_logger = None
server_logger = None

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


def get_json_schema(filepath='bounds_schema.json'):
    with open(filepath, 'r') as f:
        schema_data = f.read()
        return json.loads(schema_data)


def validate_input_json_data(json_data, json_schema):
    try:
        jsonschema.validate(json_data, json_schema)
    except jsonschema.exceptions.ValidationError:
        return None
    return json_data
