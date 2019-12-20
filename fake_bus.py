import json
import os
import random
import sys
from functools import partial

import helpers
import trio
from helpers import generate_unical_hash, install_logs_parameters
from trio_websocket import open_websocket_url


def generate_bus_id(route_id, bus_index):
    return f"{route_id}-{bus_index}"


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(url, bus_id, route):
    while True:
        coordinates = route['coordinates']
        start_offset = coordinates.index(random.choice(list(coordinates)))
        bus_coordinates = coordinates[start_offset:]
        for bus_coordinate in bus_coordinates:
            try:
                async with open_websocket_url(url) as ws:
                    lat, lng = bus_coordinate
                    broadcast_logger.info(f'{lat} {lng}')
                    await ws.send_message(
                        json.dumps(
                            {
                                "busId": bus_id,
                                "lat": lat,
                                "lng": lng,
                                "route": route['name']
                            },
                            ensure_ascii=False)
                    )
                    await trio.sleep(helpers.PAUSE_DUR)
            except OSError as ose:
                   print('Connection attempt failed: %s' % ose, file=sys.stderr)


async def start_buses():
    async with trio.open_nursery() as nursery:
        for _buses_qty in range(10, random.randint(20, 25)):
            for raw_route in load_routes():
                bus_id = generate_bus_id(raw_route['name'], generate_unical_hash())
                handler = partial(run_bus, url='ws://127.0.0.1:8080/ws',
                                  bus_id=bus_id, route=raw_route)
                nursery.start_soon(handler)


def main():
    global broadcast_logger
    broadcast_logger = install_logs_parameters(True)
    trio.run(start_buses)


if __name__ == '__main__':
    main()
