import argparse
import functools
import itertools
import json
import trio
import os
import random

import helpers
import settings
from helpers import install_logs_parameters
from trio_websocket import ConnectionClosed, HandshakeError
from trio_websocket import open_websocket_url


def get_serialized_bus_info(route, bus_id):

    coordinates = route['coordinates']
    start_offset = coordinates.index(random.choice(list(coordinates)))
    # endless cycle with offset
    route_chain = itertools.chain(coordinates[start_offset:],
                                  coordinates[::-1])
    bus_id = f"r{route['name']}/id{bus_id}/o{start_offset}"
    for bus_coordinate in itertools.cycle(route_chain):
        lat, lng = bus_coordinate
        yield json.dumps({"busId": bus_id,
                          "lat": lat,
                          "lng": lng,
                          "route": route['name']},
                         ensure_ascii=False)


def load_routes(directory_path='routes'):
    all_routes = os.listdir(directory_path)
    chosen_routes = all_routes[:_settings.routes_number]
    for filename in chosen_routes:
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(url, route, bus_id):
    first_run = True
    while True:
        if first_run:
            for serialized_bus_info in get_serialized_bus_info(route, bus_id):
                try:
                    async with open_websocket_url(url) as ws:
                        # helpers.broadcast_logger.info(f'{serialized_bus_info}')
                        if 'busId' in serialized_bus_info:  # Connection success
                            helpers.conn_attempt = 0
                        await ws.send_message(serialized_bus_info)
                    await trio.sleep(_settings.refresh_timeout)
                    first_run = False
                except OSError as e:
                    helpers.broadcast_logger.info(f'Connection failed: {e}')


def relaunch_on_disconnect(async_function):
    @functools.wraps(async_function)
    async def wrapper(*args):
        helpers.conn_attempt = 0
        while True:
            try:
                await async_function(*args)
            except (Exception, trio.MultiError) as err:
                if isinstance(err, HandshakeError) or \
                        isinstance(err, ConnectionClosed) \
                        or isinstance(err, OSError):
                    helpers.conn_attempt += 1
                    helpers.broadcast_logger.info(f'Relaunch on disconnect: '
                                                  f'{helpers.conn_attempt=}')
                if helpers.conn_attempt > 4:
                    helpers.broadcast_logger.info(f'Connection failed')
                    break
            await trio.sleep(_settings.refresh_timeout)
    return wrapper


@relaunch_on_disconnect
async def send_updates(url, receive_channel):
    async with open_websocket_url(url) as ws:
        async for bus_json in receive_channel:
            await trio.sleep(_settings.refresh_timeout)
            await ws.send_message(bus_json)


async def start_buses():
    all_buses = 0
    all_channels = {}
    url = _settings.server
    for key, free_open_memory_channel \
            in enumerate(range(_settings.websockets_number)):
        all_channels[key] = trio.open_memory_channel(0)

    async with trio.open_nursery() as nursery:

        for websocket in range(_settings.websockets_number):
            current_channel = random.choice(list(all_channels))
            send_channel, receive_channel = all_channels[current_channel]

        nursery.start_soon(send_updates, url, receive_channel)

        for route in load_routes():
            for bus in range(_settings.buses_per_route):
                all_buses += 1
                bus_id = f'{all_buses} / {route["name"]}'
                nursery.start_soon(run_bus, url, route, bus_id)
                helpers.broadcast_logger.info(f'{bus_id=}')

        await trio.sleep(_settings.refresh_timeout)


def get_args_parser():
    parser = argparse.ArgumentParser(formatter_class=
                                     argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-server', default=settings.SERVER)
    parser.add_argument('-routes_number', type=int,
                        default=settings.ROUTES_NUMBER)
    parser.add_argument('-buses_per_route', type=int,
                        default=settings.BUSES_PER_ROUTE)
    parser.add_argument('-websockets_number', type=int,
                        default=settings.WEBSOCKETS_NUMBER)
    parser.add_argument('-emulator_id',
                        default=settings.EMULATOR_ID)
    parser.add_argument('-refresh_timeout', type=int,
                        default=settings.REFRESH_TIMEOUT)
    parser.add_argument('-v', action='store_true',
                        default=settings.V, help='info logs on')
    return parser


def main():
    global _settings
    _settings = get_args_parser().parse_args()
    helpers.broadcast_logger = install_logs_parameters(_settings.v)
    trio.run(start_buses)


if __name__ == '__main__':
    main()
