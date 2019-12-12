import json
import os
import sys
from functools import partial

import helpers
import trio
from trio_websocket import open_websocket_url


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(url, bus_id=None, route=None):
    while True:
        bus_coordinates = route['coordinates']
        for bus_coordinate in bus_coordinates:
            try:
                async with open_websocket_url(url) as ws:
                    lat, lng = bus_coordinate
                    await ws.send_message(
                        json.dumps(
                            {
                                "busId": route['name'],
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
        for raw_route in load_routes():
            handler = partial(run_bus, url='ws://127.0.0.1:8080/ws',
                              bus_id=None, route=raw_route)
            nursery.start_soon(handler)


def main():
    trio.run(start_buses)


if __name__ == '__main__':
    main()
