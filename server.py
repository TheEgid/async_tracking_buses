import json

import trio
from trio_websocket import serve_websocket, ConnectionClosed


async def echo_server(request):
    ws = await request.accept()
    while True:
        try:
            raw_response = await ws.get_message()
            response = json.loads(raw_response)
            #print(response)
            print(response['buses'][0])
        except ConnectionClosed:
            break


async def main():
    await serve_websocket(echo_server, '127.0.0.1', 8080, ssl_context=None)

#open_chrome_browser()
trio.run(main)


