import json
import trio
import logging
from os import getenv
from dotenv import load_dotenv
import asyncclick as click
import contextlib
from trio_websocket import ConnectionClosed, ConnectionRejected
from trio_websocket import serve_websocket

from harmful_bus import bus_id_json_schema, bounds_json_schema, \
    validate_bus_id, validate_bounds
from helpers import Bus, WindowBounds, BusesOnBoundsFilter
import helpers


logger = logging.getLogger(__file__)


async def output_to_browser(ws):
    with contextlib.suppress(KeyError, AttributeError):
        buses_is_inside = [bus for bus_id, bus in helpers.BUSES.items() if
                           helpers.windows_bounds.is_inside(bus.lat, bus.lng)]
        output_buses_info = {
            "msgType": "Buses",
            "buses": [
                {
                    "busId": bus.busId,
                    "lat": bus.lat,
                    "lng": bus.lng,
                    "route": bus.route
                }
                for bus in buses_is_inside]
        }
        logger.info(f'buses on bounds: {len(buses_is_inside)}')
        await ws.send_message(json.dumps(output_buses_info))


async def listen_browser(ws):
    with contextlib.suppress(ConnectionClosed,
                             ConnectionRejected, json.JSONDecodeError):
        while True:
            raw_bounds = await ws.get_message()
            bounds = await validate_bounds(
                json.loads(raw_bounds), bounds_json_schema)
            if 'errors' in bounds:
                await ws.send_message(bounds)
                logger.error(str(bounds))
            helpers.windows_bounds = WindowBounds(**bounds["data"])


async def talk_to_browser(ws):
    while True:
        with contextlib.suppress(ConnectionClosed, ConnectionRejected):
            await output_to_browser(ws)
            await trio.sleep(settings['refresh_timeout'])


async def handle_browser(request):
    ws = await request.accept()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws)
        nursery.start_soon(talk_to_browser, ws)


async def handle_buses_routes(request):
    ws = await request.accept()
    with contextlib.suppress(ConnectionClosed,
                             ConnectionRejected, json.JSONDecodeError):
        while True:
            raw_response = await ws.get_message()
            input_bus_info = await validate_bus_id(
                json.loads(raw_response), bus_id_json_schema)
            if 'errors' in input_bus_info:
                await ws.send_message(input_bus_info)
                logger.error(str(input_bus_info))
            bus = Bus(**input_bus_info)
            helpers.BUSES.update({bus.busId: bus})


@click.command(load_dotenv())
@click.option('-r', '--refresh_timeout', type=float,
              default=getenv("REFRESH_TIMEOUT"),
              help='refresh in seconds', show_default=True)
@click.option('-l', '--logs', type=bool, default=getenv("LOGS"),
              help='enable logging', show_default=True)
@click.option('-b', '--buses_logs', type=bool, default=getenv("BUS_LOGS"),
              help='enable buses on boards logging', show_default=True)
async def main(**args):
    global settings
    settings = args
    _refresh_timeout = 0
    logging.basicConfig(format='%(asctime)s\t %(filename)s %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
    if settings['logs']:
        logger.disabled = False
    if settings['buses_logs']:
        logger.addFilter(BusesOnBoundsFilter())
    async with trio.open_nursery() as nursery:
        nursery.start_soon(serve_websocket, handle_buses_routes,
                           '127.0.0.1', 8080, None)
        nursery.start_soon(serve_websocket, handle_browser,
                           '127.0.0.1', 8000, None)


if __name__ == '__main__':
    with contextlib.suppress(KeyboardInterrupt):
        main(_anyio_backend="trio")
