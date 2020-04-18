# Автобусы на карте Москвы

Веб-приложение показывает передвижение автобусов на карте Москвы.

<img src="screenshots/buses.gif">

## Как установить

Скачиваем файлы. Переходим в папку с файлами.

Python>=3.8.0 должен быть уже установлен. Для установки зависимостей рекомендуется создать виртуальное окружение. Затем используйте pip для установки зависимостей:

```
pip install -r requirements.txt
```

## Переменные окружения

Настройки берутся из переменных окружения. Чтобы их определить, создайте файл `.env` рядом с `helpers.py` и запишите туда данные в таком формате: `ПЕРЕМЕННАЯ=значение`.
Доступны 7 переменных:

- `SERVER` - адрес сервера вебсокетов, пример `ws://127.0.0.1:8080/ws`
- `ROUTES_NUMBER` - количество маршрутов автобусов
- `BUSES_PER_ROUTE` - количество автобусов на одном маршруте
- `WEBSOCKETS_NUMBER` - количество задействованных вебсокетов
- `EMULATOR_ID` префикс айди автобуса, например `е`
- `REFRESH_TIMEOUT` - таймаут обновлений (в секундах)
- `V` - вывод логов в консоль, например `True`

## Запуск

Открываем в браузере файл index.html
Параллельно запускаем -

```
python fake_bus.py
```
```
python server.py
```

## Запуск с аргументами, аргументы имеют параметры по умолчанию из .env файла.

**Usage: fake_bus.py [OPTIONS]**

- `Options:`

`  -s, --server TEXT               server address  [default: ws://127.0.0.1:8080/ws]`

`  -r, --routes_number INTEGER     amount of routes  [default: 70]`

`  -b, --buses_per_route INTEGER   amount of buses on the 1 route  [default: 2]`

`  -w, --websockets_number INTEGER amount of sockets  [default: 10]`

`  -e, --emulator_id TEXT          text prefix id bus emulation  [default: e]`

`  -r, --refresh_timeout FLOAT     refresh in seconds  [default: 0.1]`

`  -l, --logs BOOLEAN              enable logging  [default: True]`

`  --help                          Show this message and exit.`


**Usage: server.py [OPTIONS]**

- `Options:`

`  -r, --refresh_timeout FLOAT     refresh in seconds  [default: 0.1]`

`  -l, --logs BOOLEAN              enable logging  [default: True]`

`  --help                          Show this message and exit.`


## Настройки в браузере

Внизу справа на странице можно включить отладочный режим логгирования и указать нестандартный адрес веб-сокета.

<img src="screenshots/settings.png">

Настройки сохраняются в Local Storage браузера и не пропадают после обновления страницы. Чтобы сбросить настройки удалите ключи из Local Storage с помощью Chrome Dev Tools —> Вкладка Application —> Local Storage.

Если что-то работает не так, как ожидалось, то начните с включения отладочного режима логгирования.


## Формат данных

Фронтенд ожидает получить от сервера JSON сообщение со списком автобусов:

```JS
{'Buses',
  buses: [
    {
      busId: 'c790сс', lat: 55.7500, lng: 37.600, route: '120',
    },
    {
      busId: 'a134aa', lat: 55.7494, lng: 37.621, route: '670к',
    },
  ],
}
```

Те автобусы, что не попали в список `buses` последнего сообщения от сервера будут удалены с карты.

Фронтенд отслеживает перемещение пользователя по карте и отправляет на сервер новые координаты окна:

```js
{
  "msgType": "newBounds",
  "data": {
    "east_lng": 37.65563964843751,
    "north_lat": 55.77367652953477,
    "south_lat": 55.72628839374007,
    "west_lng": 37.54440307617188,
  },
}
```



## Используемые библиотеки

- [Leaflet](https://leafletjs.com/) — отрисовка карты
- [loglevel](https://www.npmjs.com/package/loglevel) для логгирования


## Цели проекта

Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).
