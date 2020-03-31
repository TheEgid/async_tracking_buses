import argparse
import functools
import itertools
import json
import trio
import os
import random
from contextlib import suppress

import helpers
from helpers import install_logs_parameters, load_settings
from trio_websocket import ConnectionClosed, HandshakeError
from trio_websocket import open_websocket_url


def get_serialized_bus_info(route, bus_id):
    coordinates = route['coordinates']
    start_offset = coordinates.index(random.choice(list(coordinates)))
    # endless cycle with offset
    route_chain = itertools.chain(coordinates[start_offset:],
                                  coordinates[::-1])
    bus_id = f"r{route['name']}|id{bus_id}|o{start_offset}"
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


async def run_bus(send_channel, server_address, route, bus_id):
    first_run = True
    while True:
        if first_run:
            for serialized_bus_info in get_serialized_bus_info(route, bus_id):
                try:
                    async with open_websocket_url(server_address) as ws:
                        async with send_channel:
                            if 'busId' in serialized_bus_info:  # good connect
                                helpers.conn_attempt = 0
                            await ws.send_message(serialized_bus_info)
                        await trio.sleep(_settings.refresh_timeout)
                    first_run = False
                except (OSError, HandshakeError) as e:
                    first_run = True
                    helpers.broadcast_logger.info(f'Connection failed: {e=}')


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
async def send_updates(server_address, receive_channel):
    async with open_websocket_url(server_address) as ws:
        async for json_msg in receive_channel:
            await trio.sleep(_settings.refresh_timeout)
            await ws.send_message(json_msg)


async def start_buses():
    all_buses = 0
    all_channels = []
    server_address = _settings.server
    for _ in range(_settings.websockets_number):
        all_channels.append(trio.open_memory_channel(0))

    async with trio.open_nursery() as nursery:

        for route in load_routes():
            for websocket in range(_settings.websockets_number):
                send_channel, receive_channel = random.choice(all_channels)

            for bus in range(_settings.buses_per_route):
                all_buses += 1
                bus_id = f'{all_buses}|{route["name"]}'

                nursery.start_soon(run_bus, send_channel, server_address, route, bus_id)
                helpers.broadcast_logger.info(f'{_settings.emulator_id}{bus_id}')

        nursery.start_soon(send_updates, server_address, receive_channel)

        await trio.sleep(0)


def get_args_parser():
    settings = load_settings()
    print(settings['SERVER'])
    parser = argparse.ArgumentParser(formatter_class=
                                     argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-server', default=settings['SERVER'])
    parser.add_argument('-routes_number', type=int,
                        default=settings['ROUTES_NUMBER'])
    parser.add_argument('-buses_per_route', type=int,
                        default=settings['BUSES_PER_ROUTE'])
    parser.add_argument('-websockets_number', type=int,
                        default=settings['WEBSOCKETS_NUMBER'])
    parser.add_argument('-emulator_id',
                        default=settings['EMULATOR_ID'])
    parser.add_argument('-refresh_timeout', type=float,
                        default=settings['REFRESH_TIMEOUT'])
    parser.add_argument('-v', action='store_true',
                        default=settings['V'], help='info logs on')
    return parser


def main():
    global _settings
    _settings = get_args_parser().parse_args()
    helpers.broadcast_logger = install_logs_parameters(_settings.v)
    trio.run(start_buses)


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        main()
