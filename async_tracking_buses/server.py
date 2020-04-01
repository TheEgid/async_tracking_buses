import json
import trio
from contextlib import suppress
from trio_websocket import ConnectionClosed, ConnectionRejected
from trio_websocket import serve_websocket

from harmful_bus import validate_bus_id_json, validate_bounds_json
from helpers import Bus, WindowBounds, install_logs_parameters
from helpers import load_settings
import helpers


async def output_to_browser(ws):
    outputed_buses = set()
    try:
        buses_is_inside = \
            [bus for bus_id, bus in helpers.BUSES.items() if
             helpers.windows_bounds.is_inside(bus.lat, bus.lng)]

        output_buses_info = {"msgType": "Buses", "buses": [
            {"busId": bus.busId, "lat": bus.lat, "lng": bus.lng,
             "route": bus.route}
            for bus in buses_is_inside]}

        [outputed_buses.add(bus.busId) for bus in buses_is_inside]

        helpers.server_logger.info(f'buses on bounds: {len(outputed_buses)}')
        await ws.send_message(json.dumps(output_buses_info))
        await trio.sleep(settings.REFRESH_TIMEOUT)
    except (KeyError, AttributeError):
        pass


async def handle_browser(request):
    ws = await request.accept()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws)
        nursery.start_soon(talk_to_browser, ws)


async def listen_browser(ws):
    while True:
        try:
            raw_bounds = await ws.get_message()
            bounds = validate_bounds_json(json.loads(raw_bounds))
            if 'errors' in bounds:
                helpers.server_logger.info(**bounds['errors'])
            helpers.windows_bounds = WindowBounds(**bounds["data"])
            await trio.sleep(1)
        except (ConnectionClosed, ConnectionRejected):
            break


async def talk_to_browser(ws):
    while True:
        try:
            await output_to_browser(ws)
            await trio.sleep(float(settings['REFRESH_TIMEOUT']))
        except (ConnectionClosed, ConnectionRejected):
            break


async def handle_server(request):
    ws = await request.accept()
    while True:
        try:
            raw_response = await ws.get_message()
            input_bus_info = validate_bus_id_json(json.loads(raw_response))
            if 'errors' in input_bus_info:
                helpers.server_logger.info(input_bus_info['errors'])
            bus = Bus(**input_bus_info)
            helpers.BUSES.update({bus.busId: bus})
        except (ConnectionClosed, ConnectionRejected):
            break


async def main():
    global settings
    settings = load_settings()
    helpers.server_logger = install_logs_parameters(True)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(serve_websocket, handle_server,
                           '127.0.0.1', 8080, None)
        nursery.start_soon(serve_websocket, handle_browser,
                           '127.0.0.1', 8000, None)


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        trio.run(main)
