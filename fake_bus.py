import json
from sys import stderr

import trio
from trio_websocket import open_websocket_url


async def main():
    try:
        async with open_websocket_url('ws://127.0.0.1:8080/ws') as ws:
               ## #await ws.send_message('hello world!')
            while True:
                raw_response = await ws.get_message()
                response = json.loads(raw_response)
                print(response['buses'][0])
    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)

trio.run(main)


