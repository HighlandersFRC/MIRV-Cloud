from fastapi_socketio import SocketManager
import logging
import datetime
import schema_validation
from rover_state import Rover
from garage_state import Garage
ISO_8601_FORMAT_STRING = "%Y-%m-%dT%H:%M:%SZ"

logging.basicConfig(
    format='%(levelname)-8s [%(asctime)s|%(filename)s:%(lineno)d] %(message)s',
    datefmt=ISO_8601_FORMAT_STRING,
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)

DEVICE_TYPE_ROVER = "ROVER"
DEVICE_TYPE_GARAGE = "GARAGE"


class MirvSocketManager():
    def __init__(self, app, keycloakClient):
        self.sm = SocketManager(app=app)
        self.rovers = []
        self.garages = []
        self.keycloakClient = keycloakClient

        @self.sm.on('connect')
        async def handle_connect(sid, environ, auth):
            # Make all headers uppercase
            headers = environ

            token = auth.get('token')
            device_id = headers.get('HTTP_ID')
            device_type = headers.get('HTTP_DEVICE_TYPE', '').upper()

            if not token:
                logger.info(
                    f"Rejected Connection from: {sid}. No Authorization Header present")
                raise ConnectionRefusedError('No Authorization Header present')
            else:
                if not self.keycloakClient.validate_token_device(token):
                    logger.info(
                        f"Rejected Connection from: {sid}. Invalid Token")
                    raise ConnectionRefusedError('Invalid Token')

            if not device_id:
                logger.info(
                    f"Rejecting connection request. No device id was specified")
                raise ConnectionRefusedError(
                    'No device id. Please specify a device id with key id')

            if device_type.upper() == DEVICE_TYPE_ROVER:
                if ([i for i in self.rovers if i.rover_id == device_id]):
                    logger.info(
                        f"Rejecting connection request. Rover with id {device_id} already exists")
                    raise ConnectionRefusedError(
                        f'Rover with id {device_id} already exists')
                self.rovers.append(Rover(device_id, sid))
                logger.info(f"Connected sid: {sid}")
                logger.debug(f"{len(self.rovers)} Rover(s) connected")
            elif device_type.upper() == DEVICE_TYPE_GARAGE:
                if ([i for i in self.garages if i.garage_id == device_id]):
                    logger.info(
                        f"Rejecting connection request. Garage with id {device_id} already exists")
                    raise ConnectionRefusedError(
                        f'Garage with id {device_id} already exists')

                self.garages.append(Garage(device_id, sid))
                logger.info(f"Connected sid: {sid}")
                logger.debug(f"{len(self.garages)} Garages(s) connected")
            else:
                ConnectionRefusedError(
                    f'Device type {device_type} not recognized. Expected one of {[DEVICE_TYPE_ROVER, DEVICE_TYPE_GARAGE]}')

        @self.sm.on('data')
        async def handle_data(sid, new_state):
            logger.debug(
                f"Received {new_state} from sid: {sid} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
            if schema_validation.validate_schema(new_state, schema_validation.ROVER_STATE_SCHEMA):
                for r in self.rovers:
                    if r.sid == sid:
                        if new_state.get('rover_id') == r.rover_id:
                            r = r.update(new_state)
                            logger.info(
                                f"Successfully updated state of rover {r.rover_id}")
                            return
                        else:
                            logger.info(
                                f"Incorrect rover id for connection. Expected rover_id: {r.rover_id}")
                            await self.sm.emit('exception', 'ERROR-incorrect rover id')
                            return
                logger.info(f"Rover not found for sid. Please reconnect")
                await self.sm.emit('exception', 'RECONNECT-sid not found')
            else:
                logger.info(f"Invalid data sent to websocket")
                await self.sm.emit('exception', 'ERROR-invalid message')

        @self.sm.on('data_specific')
        async def handle_data(sid, new_state):
            logger.debug(
                f"Received {new_state} from sid: {sid} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
            try:
                for r in self.rovers:
                    if r.sid == sid:
                        r.update_individual(new_state)
                        logger.info(
                            f"Successfully updated state of rover {r.rover_id}")
                        return
                    else:
                        logger.info(
                            f"Incorrect rover id for connection. Expected rover_id: {r.rover_id}")
                        await self.sm.emit('exception', 'ERROR-incorrect rover id')
                        return
                logger.info(f"Rover not found for sid. Please reconnect")
                await self.sm.emit('exception', 'RECONNECT-sid not found')
            except:
                logger.info(f"Invalid data sent to websocket")
                await self.sm.emit('exception', 'ERROR-invalid message')

        @self.sm.on('disconnect')
        async def handle_disconnect(sid):
            logger.debug(
                f"Received disconnect request from sid: {sid} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
            for i in range(len(self.rovers)):
                if self.rovers[i].sid == sid:
                    self.rovers.pop(i)
                    logger.info(f"Disconnected sid: {sid}")
                    return

            for i in range(len(self.garages)):
                if self.garages[i].sid == sid:
                    self.garages.pop(i)
                    logger.info(f"Disconnected sid: {sid}")
                    return

            logger.info(
                f"Unable to close connection for sid: {sid}, connection does not exist")
            await self.sm.emit('exception', 'RECONNECT-sid not found')
