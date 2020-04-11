import json
import trio
from os import getenv
from dotenv import load_dotenv
import asyncclick as click
from contextlib import suppress
from trio_websocket import ConnectionClosed, ConnectionRejected
from trio_websocket import serve_websocket

from harmful_bus import bus_id_json_schema, bounds_json_schema, \
    validate_bus_id_json, validate_bounds_json
from helpers import Bus, WindowBounds, configure_logs_parameters
import helpers


server_logger = configure_logs_parameters()


async def output_to_browser(ws):
    outputed_buses = set()
    server_logger.addFilter(helpers.BusesOnBoundsFilter())
    try:
        buses_is_inside = \
            [bus for bus_id, bus in helpers.BUSES.items() if
             helpers.windows_bounds.is_inside(bus.lat, bus.lng)]

        output_buses_info = {"msgType": "Buses", "buses": [
            {"busId": bus.busId, "lat": bus.lat, "lng": bus.lng,
             "route": bus.route}
            for bus in buses_is_inside]}

        [outputed_buses.add(bus.busId) for bus in buses_is_inside]

        server_logger.info(f'buses on bounds: {len(outputed_buses)}')
        await ws.send_message(json.dumps(output_buses_info))

    except (KeyError, AttributeError):
        pass


async def listen_browser(ws):
    while True:
        try:
            raw_bounds = await ws.get_message()
            bounds = await validate_bounds_json(
                json.loads(raw_bounds), bounds_json_schema)
            if 'errors' in bounds:
                server_logger.info(**bounds['errors'])
            helpers.windows_bounds = WindowBounds(**bounds["data"])
            await trio.sleep(1)
        except (ConnectionClosed, ConnectionRejected):
            await trio.sleep(1)
            break


async def talk_to_browser(ws):
    while True:
        try:
            await output_to_browser(ws)
            await trio.sleep(settings['refresh_timeout'])
        except (ConnectionClosed, ConnectionRejected):
            break


async def handle_browser(request):
    ws = await request.accept()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws)
        nursery.start_soon(talk_to_browser, ws)


async def handle_buses_routes(request):
    ws = await request.accept()
    while True:
        try:
            raw_response = await ws.get_message()
            input_bus_info = await validate_bus_id_json(
                json.loads(raw_response), bus_id_json_schema)

            if 'errors' in input_bus_info:
                server_logger.info(input_bus_info['errors'])

            bus = Bus(**input_bus_info)
            helpers.BUSES.update({bus.busId: bus})
        except (ConnectionClosed, ConnectionRejected):
            break


@click.command(load_dotenv())
@click.option('-refresh_timeout', type=float, default=getenv("REFRESH_TIMEOUT"))
@click.option('-logs', type=bool, default=getenv("V"))
async def main(**args):
    global settings
    settings = args
    _refresh_timeout = 0
    if not settings['logs']:
        server_logger.disabled = True
    async with trio.open_nursery() as nursery:
        nursery.start_soon(serve_websocket, handle_buses_routes,
                           '127.0.0.1', 8080, None)
        nursery.start_soon(serve_websocket, handle_browser,
                           '127.0.0.1', 8000, None)


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        main(_anyio_backend="trio")
