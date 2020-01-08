import json

import helpers
import trio
from helpers import Bus
from helpers import install_logs_parameters, validate_input_json_data, \
    get_json_schema
from trio_websocket import ConnectionClosed, ConnectionRejected
from trio_websocket import serve_websocket


async def output_to_browser(ws):
    outputed_buses = set()
    try:
        buses_is_inside = \
            [bus for bus_id, bus in helpers.BUSES.items() if
             is_inside(helpers.WINDOWS_BOUNDS, bus.lat, bus.lng)]

        output_buses_info = {"msgType": "Buses", "buses": [
            {"busId": bus.busId, "lat": bus.lat, "lng": bus.lng,
             "route": bus.route}
            for bus in buses_is_inside]}

        [outputed_buses.add(bus.busId) for bus in buses_is_inside]

        helpers.server_logger.info(f'buses on bounds: {len(outputed_buses)}')
        await ws.send_message(json.dumps(output_buses_info))
        await trio.sleep(0.2)
    except KeyError:
        pass


def is_inside(bounds, lat, lng):
    is_inside_lat = bounds['south_lat'] < lat < bounds['north_lat']
    is_inside_lng = bounds['west_lng'] < lng < bounds['east_lng']
    return all([is_inside_lat, is_inside_lng])


async def handle_browser(request):
    ws = await request.accept()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws)
        nursery.start_soon(talk_to_browser, ws)


async def listen_browser(ws):
    while True:
        try:
            listened = await ws.get_message()
            bounds = validate_input_json_data(json.loads(listened),
                                              helpers.json_schema)
            if bounds:
                helpers.WINDOWS_BOUNDS.update(bounds['data'])
            await trio.sleep(0.2)
        except (ConnectionClosed, ConnectionRejected):
            break


async def talk_to_browser(ws):
    while True:
        try:
            await output_to_browser(ws)
            await trio.sleep(0.2)           # helpers.PAUSE_DUR
        except (ConnectionClosed, ConnectionRejected):
            break


async def handle_server(request):
    ws = await request.accept()
    while True:
        try:
            raw_response = await ws.get_message()
            input_bus_info = json.loads(raw_response)
            bus = Bus(**input_bus_info)
            helpers.BUSES.update({bus.busId: bus})
        except (ConnectionClosed, ConnectionRejected):
            break


async def main():
    global maximum_buses_qty
    maximum_buses_qty = 20000

    helpers.json_schema = get_json_schema()
    helpers.server_logger = install_logs_parameters(True)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(serve_websocket, handle_server, '127.0.0.1', 8080, None)
        nursery.start_soon(serve_websocket, handle_browser, '127.0.0.1', 8000, None)


if __name__ == '__main__':
    trio.run(main)

