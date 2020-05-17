import json
import jsonschema
import pytest

from helpers import get_json_schema


bus_id_json_schema = get_json_schema('schemas/bus_id_schema.json')
bounds_json_schema = get_json_schema('schemas/bounds_schema.json')


async def validate_bounds(bounds, bounds_schema_json):
    error_msg = json.dumps(
        {
            "errors": ["Requires valid JSON"],
            "msgType": "Errors"
        },
        ensure_ascii=False)
    try:
        jsonschema.validate(bounds, bounds_schema_json)
    except jsonschema.exceptions.ValidationError:
        return error_msg
    return bounds


async def validate_bus_id(bus_id, bus_id_schema_json):
    error_msg = json.dumps(
        {
            "errors": ["Requires busId specified"],
            "msgType": "Errors"
        },
        ensure_ascii=False)
    try:
        jsonschema.validate(bus_id, bus_id_schema_json)
    except jsonschema.exceptions.ValidationError:
        return error_msg
    return bus_id


@pytest.fixture(scope="class")
def bad_bounds(request):
        yield json.dumps(
            {
                "msgType": "newBounds",
                "data":
                    {"south_lat": '55.75460588316582',
                     "north_lat": 55.78844965172979,
                     "west_lng": 37.42655754089356,
                     "east_lng": 37.55839347839356}
            },
            ensure_ascii=False)


@pytest.fixture(scope="class")
def bad_bus_id(request):
        yield json.dumps(
            {
                "busId": "",
                "lat": 55.591238932907,
                "lng": 37.664172757715,
                "route": 162
            },
            ensure_ascii=False)


class TestBusData:

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("bad_bounds")
    async def test_validate_bounds_json(self, bad_bounds):
        _result = await validate_bounds(json.loads(bad_bounds),
                                        bounds_json_schema)
        result = json.loads(_result)
        assert isinstance(result, dict)
        assert result['errors'] == ['Requires valid JSON']

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("bad_bus_id")
    async def test_validate_bus_id_json(self, bad_bus_id):
        _result = await validate_bus_id(json.loads(bad_bus_id),
                                        bus_id_json_schema)
        result = json.loads(_result)
        assert isinstance(result, dict)
        assert result['errors'] == ['Requires busId specified']


if __name__ == '__main__':
    pytest.main([__file__, '--capture=sys', '--tb=line', '-v'])
