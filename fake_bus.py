import json
import os
import random
import sys
from functools import partial
from trio_websocket import open_websocket_url
import trio
from helpers import install_logs_parameters
import helpers
import settings


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
                    await trio.sleep(args.refresh_timeout)
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
                for bus_per_route in range(args.buses_per_route):
                    current_channel = random.choice(list(all_channels))
                    send_channel, receive_channel = all_channels[current_channel]
                    bus_id = _buses_qty
                    nursery.start_soon(transponder, url, bus_id, receive_channel)
                    await send_channel.send(raw_route)


async def start_buses():
    all_channels = {}
    url = args.server
    for id, free_open_memory_channel in enumerate(range(args.websockets_number)):
        all_channels[id] = trio.open_memory_channel(0)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(send_updates, url, all_channels)


def get_args_parser():
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(formatter_class=formatter_class)
	
    parser.add_argument('-server', default=settings.SERVER)
    parser.add_argument('-routes_number', type=int, default=settings.ROUTES_NUMBER)
    parser.add_argument('-buses_per_route', type=int, default=settings.BUSES_PER_ROUTE)
    parser.add_argument('-websockets_number', type=int, default=settings.WEBSOCKETS_NUMBER)
	parser.add_argument('-emulator_id', default=settings.EMULATOR_ID)
    parser.add_argument('-refresh_timeout', type=int, default=settings.REFRESH_TIMEOUT)	
    parser.add_argument('-v', action='store_true', default=settings.V, 
						help='check logs')
    return parser        


def main():
    global broadcast_logger
    broadcast_logger = install_logs_parameters(True)
    
    args = get_args_parser().parse_args()
    trio.run(start_buses)


if __name__ == '__main__':
    main()
