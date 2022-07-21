import json
import logging
import jsonschema

# Set Logging Object and Functionality
logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
l = logging.getLogger(__name__)

ROVER_STATE_SCHEMA = {}


ROVER_STATE_SCHEMA = json.loads(
    open('./schemas/rover_state_schema.json', 'r').read())


def validate_schema(obj, schema):
    if not obj or not schema:
        return False
    try:
        jsonschema.validate(instance=obj, schema=schema)
    except jsonschema.ValidationError as e:
        l.error(e)
        return False
    return True
