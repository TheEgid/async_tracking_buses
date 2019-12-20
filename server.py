import json

import helpers
import trio
from helpers import Bus
from helpers import install_logs_parameters
from trio_websocket import ConnectionClosed, ConnectionRejected
from trio_websocket import serve_websocket


async def output_to_browser(ws):
    output_buses_info = {
            "msgType": "Buses",
            "buses":  [{
                "busId": bus.busId,
                "lat": bus.lat,
                "lng": bus.lng,
                "route": bus.route
            } for bus in helpers.BUSES.values()]}
    for output_bus in output_buses_info["buses"]:
        logger_info = f'{output_bus["busId"]}'
        broadcast_logger.info(logger_info)
    await ws.send_message(json.dumps(output_buses_info))


async def talk_to_browser(request):
    ws = await request.accept()
    while True:
        try:
            await output_to_browser(ws)
            await trio.sleep(helpers.PAUSE_DUR)
        except (ConnectionClosed, ConnectionRejected):
            break


async def input_handle_server(request):
    ws = await request.accept()
    while True:
        try:
            raw_response = await ws.get_message()
            input_bus_info = json.loads(raw_response)
            #broadcast_logger.info(f'{input_bus_info=}')
            bus = Bus(**input_bus_info)
            helpers.BUSES.update({bus.busId: bus})
        except (ConnectionClosed, ConnectionRejected):
            break


async def main():
    global broadcast_logger
    broadcast_logger = install_logs_parameters(True)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(serve_websocket, input_handle_server, '127.0.0.1', 8080, None)
        nursery.start_soon(serve_websocket, talk_to_browser, '127.0.0.1', 8000, None)


#open_chrome_browser()
trio.run(main)


