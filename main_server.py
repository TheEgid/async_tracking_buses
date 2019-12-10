import json
import trio
from trio_websocket import serve_websocket, ConnectionClosed
from helpers import open_chrome_browser

# MSG = {
#   "msgType": "Buses",
#   "buses": [
#     {"busId": "c790сс", "lat": 55.7500, "lng": 37.600, "route": "120"},
#     {"busId": "a134aa", "lat": 55.7494, "lng": 37.621, "route": "670к"},
#   ]
# }
#MSG = {"msgType": "Buses", "buses": [{"busId": "c790сс", "lat": 55.7500, "lng": 37.600, "route": "120"}]}
#MSG = {'msgType': 'Buses', 'buses': [{'busId': 'a134aa', 'lat': 55.747629944737, 'lng': 37.641726387317, 'route': '156'}]}


def get_json_route(path='156.json'):
    with open(path, 'r', encoding='utf-8') as fl:
        var_data = json.load(fl)
    return var_data


def get_route():
    raw_route = get_json_route()
    coordinates = raw_route["coordinates"]
    name = raw_route['name']
    dots = [{"busId": "a134aa",
             "lat": coordinate[0],
             "lng": coordinate[1],
             "route": name} for coordinate in coordinates]
    return [{"msgType": "Buses", "buses": [dot]} for dot in dots]


async def echo_server(request):
    print("ECHO SERVER")
    ws = await request.accept()
    while True:
        try:
            # message = await ws.get_message()
            # print(message)

            for x in get_route():
                await ws.send_message(json.dumps(x))
                await trio.sleep(1)

        except ConnectionClosed:
            break


async def start():
    await serve_websocket(echo_server, '127.0.0.1', 8080, ssl_context=None)


def main():
    open_chrome_browser()
    trio.run(start)


if __name__ == '__main__':
    main()


