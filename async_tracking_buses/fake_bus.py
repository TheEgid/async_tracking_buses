import functools
import itertools
import json
import trio
import os
import random
from contextlib import suppress
from os import getenv
from dotenv import load_dotenv
import asyncclick as click
import logging
from trio_websocket import ConnectionClosed, HandshakeError
from trio_websocket import open_websocket_url

import helpers


logger = logging.getLogger(__file__)


async def get_serialized_bus_info(route, bus_id):
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


async def load_routes(directory_path='routes'):
    all_routes = os.listdir(directory_path)
    chosen_routes = all_routes[:settings['routes_number']]
    for filename in chosen_routes:
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(send_channel, server_address, route, bus_id):
    first_run = True
    while True:
        if first_run:
            async for serialized_bus_info in get_serialized_bus_info(route,
                                                                     bus_id):
                try:
                    async with open_websocket_url(server_address) as ws:
                        async with send_channel:
                            if 'busId' in serialized_bus_info:  # good connect
                                helpers.conn_attempt = 0
                            await ws.send_message(serialized_bus_info)
                        await trio.sleep(settings['refresh_timeout'])
                    first_run = False
                except OSError as e:
                    first_run = True
                    logger.error(f'Connection failed: {e=}')
                except HandshakeError:
                    pass


def relaunch_on_disconnect(async_function):
    @functools.wraps(async_function)
    async def wrapper(*args):
        helpers.conn_attempt = 0
        while True:
            try:
                await async_function(*args)
            except (Exception, trio.MultiError) as err:
                if isinstance(err, ConnectionClosed) or \
                        isinstance(err, HandshakeError):
                    helpers.conn_attempt += 1
                    logger.error(f'Relaunch on disconnect: '
                                 f'{helpers.conn_attempt=}')
                if helpers.conn_attempt > 24:
                    logger.error(f'Connection failed')
                    break
            await trio.sleep(settings['refresh_timeout'])
    return wrapper


@relaunch_on_disconnect
async def send_updates(server_address, receive_channel):
    async with open_websocket_url(server_address) as ws:
        async for json_msg in receive_channel:
            await trio.sleep(settings['refresh_timeout'])
            await ws.send_message(json_msg)


async def start_buses():
    all_buses = 0
    all_channels = []
    server_address = settings['server']
    for _ in range(settings['websockets_number']):
        all_channels.append(trio.open_memory_channel(0))

    async with trio.open_nursery() as nursery:
        async for route in load_routes():
            for websocket in range(settings['websockets_number']):
                send_channel, receive_channel = random.choice(all_channels)
            for bus in range(settings['buses_per_route']):
                all_buses += 1
                bus_id = f'{all_buses}|{route["name"]}'
                nursery.start_soon(run_bus, send_channel, server_address, route,
                                   bus_id)
                logger.info(f"{settings['emulator_id']}{bus_id}")

        nursery.start_soon(send_updates, server_address, receive_channel)
        await trio.sleep(0)


@click.command(load_dotenv())
@click.option('-s', '--server', type=str, default=getenv("SERVER"),
              help='server address', show_default=True)
@click.option('-r', '--routes_number', type=int, default=getenv("ROUTES_NUMBER"),
              help='amount of routes', show_default=True)
@click.option('-b', '--buses_per_route', type=int,
              default=getenv("BUSES_PER_ROUTE"),
              help='amount of buses on the 1 route', show_default=True)
@click.option('-w', '--websockets_number', type=int,
              default=getenv("WEBSOCKETS_NUMBER"),
              help='amount of sockets', show_default=True)
@click.option('-e', '--emulator_id', type=str, default=getenv("EMULATOR_ID"),
              help='text prefix id bus emulation', show_default=True)
@click.option('-r', '--refresh_timeout', type=float,
              default=getenv("REFRESH_TIMEOUT"),
              help='refresh in seconds', show_default=True)
@click.option('-l', '--logs', type=bool, default=getenv("V"),
              help='enable logging', show_default=True)
async def main(**args):
    global settings
    settings = args
    logging.basicConfig(format='%(asctime)s\t %(filename)s %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
    if not settings['logs']:
        logger.disabled = True
    async with trio.open_nursery() as nursery:
        nursery.start_soon(start_buses)


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        main(_anyio_backend="trio")
