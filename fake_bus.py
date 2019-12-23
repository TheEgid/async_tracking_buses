import json
import os
import random
import sys
from functools import partial

import helpers
import trio
from helpers import install_logs_parameters
from trio_websocket import open_websocket_url


def get_serialized_bus_info(route, bus_id):
    coordinates = route['coordinates']
    start_offset = coordinates.index(random.choice(list(coordinates)))
    bus_coordinates = coordinates[start_offset:]
    bus_id = f"{bus_id} {route['name']}"
    for bus_coordinate in bus_coordinates:
        lat, lng = bus_coordinate
        yield json.dumps({"busId": bus_id,
                          "lat": lat,
                          "lng": lng,
                          "route": route['name']
                          },
                         ensure_ascii=False)


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(url, route, bus_id):
    while True:
        for serialized_bus_info in get_serialized_bus_info(route, bus_id):
            try:
                async with open_websocket_url(url) as ws:
                    broadcast_logger.info(f'{serialized_bus_info}')
                    await ws.send_message(serialized_bus_info)
                    await trio.sleep(helpers.PAUSE_DUR)
            except OSError as ose:
                print('Connection attempt failed: %s' % ose, file=sys.stderr)


async def transponder(url, bus_id, receive_channel):
    async with trio.open_nursery() as nursery:
        async for value in receive_channel:
            raw_route = dict(value)
            handler = partial(run_bus, url=url, route=raw_route, bus_id=bus_id)
            nursery.start_soon(handler)
            await trio.sleep(random.random())


async def send_updates(url, all_channels):
        async with trio.open_nursery() as nursery:
            for raw_route in load_routes():
                for _buses_qty in range(2):
                    current_channel = random.choice(list(all_channels))
                    send_channel, receive_channel = all_channels[current_channel]
                    bus_id = _buses_qty
                    nursery.start_soon(transponder, url, bus_id, receive_channel)
                    await send_channel.send(raw_route)


async def start_buses():
    possible_channels_qty = 50
    all_channels = {}
    url = 'ws://127.0.0.1:8080/ws'
    for id, free_open_memory_channel in enumerate(range(possible_channels_qty)):
        all_channels[id] = trio.open_memory_channel(0)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(send_updates, url, all_channels)


def main():
    global broadcast_logger
    broadcast_logger = install_logs_parameters(True)
    trio.run(start_buses)


if __name__ == '__main__':
    main()
