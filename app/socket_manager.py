from fastapi_socketio import SocketManager
import logging
import datetime
from schemas import mirv_schemas
from rover_state import Rover

ISO_8601_FORMAT_STRING = "%Y-%m-%dT%H:%M:%SZ"

logging.basicConfig(
    format='%(levelname)-8s [%(asctime)s|%(filename)s:%(lineno)d] %(message)s',
    datefmt=ISO_8601_FORMAT_STRING,
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


class MirvSocketManager():
    def __init__(self, app, keycloakClient):
        self.sm = SocketManager(app=app)
        self.ROVERS = []

        @self.sm.on('connect')
        async def handle_connect(sid, environ, auth):
            logger.debug(
                f"Connection request for sid: {sid} with environ: {environ}, auth: {auth}, at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
            if not environ.get("HTTP_ROVERID"):
                logger.info(
                    f"Rejecting connection request. No roverId was specified. Please specify the roverId in the headers")
                await self.sm.emit('exception', 'AUTH-no rover id')
                return
            if not keycloakClient.validate_token(auth['token']):
                logger.info(f"Rejecting connection request. Invalid token")
                await self.sm.emit('exception', 'AUTH-invalid token')
                return
            roverId = environ["HTTP_ROVERID"]
            for i in self.ROVERS:
                if i.roverId == i:
                    self.ROVERS.pop(i)
                    self.sm.disconnect(sid)
                    logger.debug(
                        f"Connection request from already connected Rover. Closing and creating new connection")
            self.ROVERS.append(Rover(roverId, sid))
            logger.info(f"Connected sid: {sid}")
            logger.debug(f"{len(self.ROVERS)} Rover(s) connected")

        @self.sm.on('data')
        async def handle_data(sid, new_state):
            logger.debug(
                f"Received {new_state} from sid: {sid} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
            if mirv_schemas.validate_schema(new_state, mirv_schemas.ROVER_STATE_SCHEMA):
                for r in self.ROVERS:
                    if r.sid == sid:
                        if new_state.get('roverId') == r.roverId:
                            r = r.update(new_state)
                            logger.info(
                                f"Successfully updated state of rover {r.roverId}")
                            return
                        else:
                            logger.info(
                                f"Incorrect rover id for connection. Expected roverId: {r.roverId}")
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
                for r in self.ROVERS:
                    if r.sid == sid:
                        r.update_individual(new_state)
                        logger.info(
                            f"Successfully updated state of rover {r.roverId}")
                        return
                    else:
                        logger.info(
                            f"Incorrect rover id for connection. Expected roverId: {r.roverId}")
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
            for i in range(len(self.ROVERS)):
                if self.ROVERS[i].sid == sid:
                    self.ROVERS.pop(i)
                    logger.info(f"Disconnected sid: {sid}")
                    return
            logger.info(
                f"Unable to close connection for sid: {sid}, connection does not exist")
            await self.sm.emit('exception', 'RECONNECT-sid not found')
