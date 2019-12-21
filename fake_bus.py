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


async def transponder(url, receive_channel):
    async with trio.open_nursery() as nursery:
        async for value in receive_channel:
            raw_route = dict(value)
            bus_id = generate_bus_id(raw_route['name'],
                                     generate_unical_hash())
            handler = partial(run_bus, url=url, bus_id=bus_id,
                              route=raw_route)
            nursery.start_soon(handler)
            await trio.sleep(random.random())


async def send_updates(send_channel):
    for _buses_qty in range(2):  # 5, random.randint(7, 10)):
        for raw_route in load_routes():
            await send_channel.send(raw_route)


async def start_buses():
    channel_qty = 10
    all_channels = list()
    url = 'ws://127.0.0.1:8080/ws'
    async with trio.open_nursery() as nursery:
        for free_open_memory_channel in range(channel_qty):
            all_channels.append([trio.open_memory_channel(0)])
        for all_channel in all_channels:
            send_channel, receive_channel = all_channel[0]
            nursery.start_soon(send_updates, send_channel)
            nursery.start_soon(transponder, url, receive_channel)


def main():
    global broadcast_logger
    broadcast_logger = install_logs_parameters(True)
    trio.run(start_buses)


if __name__ == '__main__':
    main()
