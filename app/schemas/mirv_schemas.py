import json
import logging
import jsonschema

# Set Logging Object and Functionality
logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
l = logging.getLogger(__name__)

ROVER_STATE_SCHEMA = {}
ROVER_STATE_SCHEMA_STR = '{"$schema":"http://json-schema.org/draft-04/schema#","type":"object","properties":{"roverId":{"type":"string"},"state":{"$ref":"#/definitions/rover_state_enum"},"status":{"$ref":"#/definitions/rover_status_enum"},"battery-percent":{"type":"integer"},"battery-voltage":{"type":"number"},"health":{"type":"object","properties":{"electronics":{"$ref":"#/definitions/rover_health_enum"},"drivetrain":{"$ref":"#/definitions/rover_health_enum"},"intake":{"$ref":"#/definitions/rover_health_enum"},"sensors":{"$ref":"#/definitions/rover_health_enum"},"garage":{"$ref":"#/definitions/rover_health_enum"},"power":{"$ref":"#/definitions/rover_health_enum"},"general":{"$ref":"#/definitions/rover_health_enum"}},"required":["electronics","drivetrain","intake","sensors","garage","power","general"]},"telemetry":{"type":"object","properties":{"location":{"type":"object","properties":{"lat":{"type":["integer","null"]},"long":{"type":["integer","null"]}},"required":["lat","long"]},"heading":{"type":["number","null"]},"speed":{"type":["number","null"]}},"required":["heading","speed"]}},"required":["roverId","state","status","battery-percent","battery-voltage","health","telemetry"],"definitions":{"rover_state_enum":{"enum":["disconnected","disconnected_fault","e_stop","connected_disabled","connected_idle_roaming","connected_idle_docked","connected_fault","autonomous","remote_operation"]},"rover_status_enum":{"enum":["available","unavailable"]},"rover_health_enum":{"enum":["unhealthy","degraded","healthy","unavailable"]}}}'


try:
    ROVER_STATE_SCHEMA = json.loads(ROVER_STATE_SCHEMA_STR)
except Exception as e:
    l.error(
        f"Unable to read in ROVER_STATE_SCHEMA because {e}")


def validate_schema(obj, schema):
    if not obj or not schema:
        return False
    try:
        jsonschema.validate(instance=obj, schema=schema)
    except jsonschema.ValidationError as e:
        l.error(e)
        return False
    return True
