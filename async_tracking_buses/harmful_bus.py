import json
import jsonschema
import unittest


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
        return json.loads(error_msg)
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
        return json.loads(error_msg)
    return json_data


class BasicTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bad_bounds_data = json.dumps(
            {
                "msgType": "newBounds",
                "data":
                    {"south_lat": '55.75460588316582',
                     "north_lat": 55.78844965172979,
                     "west_lng": 37.42655754089356,
                     "east_lng": 37.55839347839356}
            },
            ensure_ascii=False)

        cls.bad_bus_id_data = json.dumps(
            {
                "busId": "",
                "lat": 55.591238932907,
                "lng": 37.664172757715,
                "route": 162
            },
            ensure_ascii=False)

    def test_validate_bounds_json(self):
        result = validate_bounds_json(json.loads(self.bad_bus_id_data))
        self.assertTrue('errors' in result)
        self.assertEqual(['Requires valid JSON'],
                         dict(result)['errors'])

    def test_validate_bus_id_json(self):
        result = validate_bus_id_json(json.loads(self.bad_bus_id_data))
        self.assertTrue('errors' in result)
        self.assertEqual(['Requires busId specified'],
                         dict(result)['errors'])


if __name__ == '__main__':
    myTestSuite = unittest.TestSuite()
    myTestSuite.addTest(unittest.makeSuite(BasicTests))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(myTestSuite)
