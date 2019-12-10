import json
import os
from functools import partial
from sys import stderr

import trio
from trio_websocket import open_websocket_url


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


def serialize_route(raw_route):
    coordinates = raw_route["coordinates"]
    name = raw_route['name']
    dots = [
        {
            "busId": name,
            "lat": coordinate[0],
            "lng": coordinate[1],
            "route": name
        }
        for coordinate in coordinates
    ]
    return [{"msgType": "Buses", "buses": [dot]} for dot in dots]


async def run_bus(url, bus_id=None, route=None):
    try:
        async with open_websocket_url(url) as ws:
            for serialized_route in serialize_route(route):
                await ws.send_message(json.dumps(serialized_route,
                                                 ensure_ascii=True))
                await trio.sleep(1)
    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


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
