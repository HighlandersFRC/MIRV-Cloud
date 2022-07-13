from fastapi_socketio import SocketManager
import logging
import datetime
from fastapi import Depends
from schemas import mirv_schemas
from rover_state import Rover
from garage_state import Garage
from main import get_current_token
ISO_8601_FORMAT_STRING = "%Y-%m-%dT%H:%M:%SZ"

logging.basicConfig(
    format='%(levelname)-8s [%(asctime)s|%(filename)s:%(lineno)d] %(message)s',
    datefmt=ISO_8601_FORMAT_STRING,
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


class MirvSocketManager():
    def __init__(self, app, PASSWORD=None):
        self.sm = SocketManager(app=app)
        self.rovers = []
        self.garages = []

        @self.sm.on('connect')
        async def handle_connect(sid, environ, token_valid: bool = Depends(get_current_token)):
            keys = environ.keys()
            temp = {}
            for key in keys:
                #print(environ[key])
                temp[key.upper()] = environ[key]

            environ = temp
            if "HTTP_ROVERID" in environ:
                rover_id = environ["HTTP_ROVERID"]
                if ([i for i in self.rovers if i.rover_id == rover_id]):
                    l.info(f"Rejecting connection request. Rover id already exists")
                    await sm.emit('exception', 'ERROR-rover_id already exists')
                    return
                self.rovers.append(Rover(rover_id, sid))
                l.info(f"Connected sid: {sid}")
                l.debug(f"{len(self.rovers)} Rover(s) connected")

            if "HTTP_GARAGEID" in environ:
                garage_id = environ["HTTP_GARAGEID"]
                if ([i for i in self.garages if i.garage_id == garage_id]):
                    l.info(f"Rejecting connection request. Garage id already exists")
                    await sm.emit('exception', 'ERROR-garageID already exists')
                    return
                self.garages.append(Garage(garage_id, sid))

            if (not "HTTP_GARAGEID" in environ) and (not "HTTP_ROVERID" in environ):
                l.info(f"Rejecting connection request. No DeviceID was specified. Please specify the DeviceID in the headers")
                await sm.emit('exception', 'AUTH-no rover id')
                return 400

        @self.sm.on('data')
        async def handle_data(sid, new_state):
            l.debug(
                f"Received {new_state} from sid: {sid} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
            if mirv_schemas.validate_schema(new_state, mirv_schemas.ROVER_STATE_SCHEMA):
                for r in self.rovers:
                    if r.sid == sid:
                        if new_state.get('rover_id') == r.rover_id:
                            r = r.update(new_state)
                            l.info(f"Successfully updated state of rover {r.rover_id}")
                            return
                        else:
                            l.info(
                                f"Incorrect rover id for connection. Expected rover_id: {r.rover_id}")
                            await sm.emit('exception', 'ERROR-incorrect rover id')
                            return
                l.info(f"Rover not found for sid. Please reconnect")
                await sm.emit('exception', 'RECONNECT-sid not found')
            else:
                l.info(f"Invalid data sent to websocket")
                await sm.emit('exception', 'ERROR-invalid message')

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


