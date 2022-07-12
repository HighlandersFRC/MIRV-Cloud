from hashlib import sha256
from http.client import HTTPException
import datetime
from typing import Union, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_socketio import SocketManager
from pydantic import BaseModel
from rover_state import Rover
from garage_state import Garage
import asyncio
import os
import json
import logging
import uvicorn
from schemas import mirv_schemas
import requests

ROVERS = []
GARAGES= []
ISO_8601_FORMAT_STRING = "%Y-%m-%dT%H:%M:%SZ"

# Set Logging Object and Functionality
logging.basicConfig(
    format='%(levelname)-8s [%(asctime)s|%(filename)s:%(lineno)d] %(message)s',
    datefmt=ISO_8601_FORMAT_STRING,
    level=logging.DEBUG,
)
l = logging.getLogger(__name__)

app = FastAPI()
sm = SocketManager(app=app)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PASS = os.getenv("PASSWORD")


class ConnectionRequest(BaseModel):
    connection_id: str
    rover_id: str
    offer: dict



class ConnectionResponseValid(BaseModel):
    connection_id: str
    answer: str
    candidate: str


def get_rover_by_id(rover_id):
    for rover in ROVERS:
        if rover.rover_id == rover_id:
            return rover
    return None


##################################################################
# Socket Connection
##################################################################
@sm.on('connect')
async def handle_connect(sid, environ):
    #l.debug(
    #    f"Connection request for sid: {sid} with environ: {environ}, auth: {auth}, at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
    
    #if auth["password"] != PASS:
    #    l.info(f"Rejecting connection request. Invalid password")
    #    await sm.emit('exception', 'AUTH-invalid password')
    #    return
    

    keys = environ.keys()
    temp = {}
    for key in keys:
        #print(environ[key])
        temp[key.upper()] = environ[key]

    environ = temp
    if "HTTP_ROVERID" in environ:
        rover_id = environ["HTTP_ROVERID"]
        if ([i for i in ROVERS if i.rover_id == rover_id]):
            l.info(f"Rejecting connection request. Rover id already exists")
            await sm.emit('exception', 'ERROR-rover_id already exists')
            return
        ROVERS.append(Rover(rover_id, sid))
        l.info(f"Connected sid: {sid}")
        l.debug(f"{len(ROVERS)} Rover(s) connected")

    if "HTTP_GARAGEID" in environ:
        garage_id = environ["HTTP_GARAGEID"]
        if ([i for i in GARAGES if i.garage_id == garage_id]):
            l.info(f"Rejecting connection request. Garage id already exists")
            await sm.emit('exception', 'ERROR-garageID already exists')
            return
        GARAGES.append(Garage(garage_id, sid))

    if (not "HTTP_GARAGEID" in environ) and (not "HTTP_ROVERID" in environ):
        l.info(f"Rejecting connection request. No DeviceID was specified. Please specify the DeviceID in the headers")
        await sm.emit('exception', 'AUTH-no rover id')
        return



@sm.on('data')
async def handle_data(sid, new_state):
    l.debug(
        f"Received {new_state} from sid: {sid} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
    # try:
    #     new_state_obj = json.loads(new_state)
    # except ValueError:
    #     l.info(
    #         f"Incorrect rover id for connection. Expected rover_id: {r.rover_id}")
    #     await sm.emit('exception', 'ERROR-not json')
    #     return
    if mirv_schemas.validate_schema(new_state, mirv_schemas.ROVER_STATE_SCHEMA):
        for r in ROVERS:
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


@sm.on('data_specific')
async def handle_data(sid, new_state):
    l.debug(
        f"Received {new_state} from sid: {sid} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
    try:
        for r in ROVERS:
            if r.sid == sid:
                r.update_individual(new_state)
                l.info(f"Successfully updated state of rover {r.rover_id}")
                return
            else:
                l.info(
                    f"Incorrect rover id for connection. Expected rover_id: {r.rover_id}")
                await sm.emit('exception', 'ERROR-incorrect rover id')
                return
        l.info(f"Rover not found for sid. Please reconnect")
        await sm.emit('exception', 'RECONNECT-sid not found')
    except:
        l.info(f"Invalid data sent to websocket")
        await sm.emit('exception', 'ERROR-invalid message')


@sm.on('disconnect')
async def handle_disconnect(sid):
    l.debug(
        f"Received disconnect request from sid: {sid} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
    for i in range(len(ROVERS)):
        if ROVERS[i].sid == sid:
            ROVERS.pop(i)
            l.info(f"Disconnected sid: {sid}")
            return
    l.info(
        f"Unable to close connection for sid: {sid}, connection does not exist")
    await sm.emit('exception', 'RECONNECT-sid not found')


##################################################################
# Rest Endpoint
##################################################################
@app.get("/")
def read_root():
    l.debug(
        f"Received request to / at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
    return {"Hello": "World"}


# GET: list of rovers and statuses
@app.get("/rovers")
async def read_item(q: Union[str, None] = None):
    l.debug(
        f"Received request to /rovers at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
    return [r.getState() for r in ROVERS]

@app.get("/garages")
async def read_item(q: Union[str, None] = None):
    l.debug(
        f"Received request to /rovers at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
    return [g.getState() for g in GARAGES]


@app.get("/rovers/{rover_id}")
async def read_item(rover_id: str, q: Union[str, None] = None):
    l.debug(
        f"Received request to /rovers/{{rover_id}} with rover_id={rover_id} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
    for r in ROVERS:
        if r.rover_id == rover_id:
            return r.rover_state
    raise HTTPException(
        status_code=404, detail=f'Rover "{rover_id}" does not exist')


@app.post("/rovers/connect")
async def connect_to_rover(connection_request: ConnectionRequest):
    print('Connection')


    
    l.debug(
        f"Received request to /rovers/connect with connection_id={connection_request.connection_id} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")

    request_rover_id = connection_request.rover_id
    request_offer = connection_request.offer
    
    print(request_rover_id, request_offer)
    
    
    #Find if rover is connected to api
    rover = get_rover_by_id(request_rover_id)
    
    if rover is not None:
        # Request rover to respond to the desired connection string.
        response = await sm.call('connection_offer', data = {'offer': request_offer}, to = rover.sid, timeout = 20)
        if response is not None:
            l.debug(f"Received Response: {response} from Rover {request_rover_id} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")

            return response
        else:
            HTTPException(status_code=408, detail="Rover did not respond within allotted connection time.")
    else:
        raise HTTPException(status_code=404, detail="Rover not found")
    
    
    #x = requests.post('http://localhost:8080/offer', json = {'offer': request_offer})
    #print ("Response", x.json())

    return x.json()


@app.post("/ping/garage")
async def connect_to_rover():
    print("Sending Ping")
    for garage in GARAGES:
        response = await sm.call('connection_offer', data = {'offer': "test"}, to = garage.sid, timeout = 20)
    
    
    #x = requests.post('http://localhost:8080/offer', json = {'offer': request_offer})
    #print ("Response", x.json())

    return 200


