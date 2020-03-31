import json
import jsonschema
import unittest


class ValidationError(Exception):
    """Declare special exception."""
    pass


def get_json_schema(filepath):
    """https://jsonschema.net/home"""
    with open(filepath, 'r') as f:
        schema_data = f.read()
        return json.loads(schema_data)


def validate_bounds_json(json_data):
    error_msg = json.dumps(
        {
            "errors": ["Requires valid JSON"],
            "msgType": "Errors"
        },
        ensure_ascii=False)
    json_schema = get_json_schema('schemas/bounds_schema.json')
    try:
        jsonschema.validate(json_data, json_schema)
    except jsonschema.exceptions.ValidationError:
        raise ValidationError(json.loads(error_msg))
    return json_data


def validate_bus_id_json(json_data):
    error_msg = json.dumps(
        {
            "errors": ["Requires busId specified"],
            "msgType": "Errors"
        },
        ensure_ascii=False)
    json_schema = get_json_schema('schemas/bus_id_schema.json')
    try:
        jsonschema.validate(json_data, json_schema)
    except jsonschema.exceptions.ValidationError:
        raise ValidationError(json.loads(error_msg))
    return json_data


bad_bus_id_data = json.dumps(
    {
        "busId": "",
        "lat": 55.591238932907,
        "lng": 37.664172757715,
        "route": 162
    },
    ensure_ascii=False)


bad_bounds_data = json.dumps(
    {
        "msgType": "newBounds",
        "data":
            {"south_lat": '55.75460588316582',
             "north_lat": 55.78844965172979,
             "west_lng": 37.42655754089356,
             "east_lng": 37.55839347839356}
    },
    ensure_ascii=False)


class BasicTests(unittest.TestCase):
    def test_validate_bounds_json_exception(self):
        with self.assertRaises(ValidationError):
            validate_bounds_json(json.loads(bad_bounds_data))

    def test_validate_bus_id_json_exception(self):
        with self.assertRaises(ValidationError):
            validate_bus_id_json(json.loads(bad_bus_id_data))


            # input_bus_info = validate_bus_id_json(json.loads(raw_response))
            # if 'errors' in input_bus_info:


if __name__ == '__main__':
    myTestSuite = unittest.TestSuite()
    myTestSuite.addTest(unittest.makeSuite(BasicTests))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(myTestSuite)


