from http.client import HTTPException
import datetime
from typing import Union, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging

from socket_manager import MirvSocketManager

ISO_8601_FORMAT_STRING = "%Y-%m-%dT%H:%M:%SZ"
PASS = os.getenv("PASSWORD")

# Set Logging Object and Functionality
logging.basicConfig(
    format='%(levelname)-8s [%(asctime)s|%(filename)s:%(lineno)d] %(message)s',
    datefmt=ISO_8601_FORMAT_STRING,
    level=logging.DEBUG,
)
l = logging.getLogger(__name__)

app = FastAPI()
sm = MirvSocketManager(app, PASS)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionRequest(BaseModel):
    connection_id: str
    rover_id: str
    offer: dict


class ConnectionResponseValid(BaseModel):
    connection_id: str
    answer: str
    candidate: str


def get_rover_by_id(rover_id):
    for rover in sm.ROVERS:
        if rover.roverId == rover_id:
            return rover
    return None


##################################################################
# Socket Connection
##################################################################


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
    return [r.getState() for r in sm.ROVERS]


@app.get("/rovers/{roverId}")
async def read_item(roverId: str, q: Union[str, None] = None):
    l.debug(
        f"Received request to /rovers/{{roverId}} with roverId={roverId} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
    for r in sm.ROVERS:
        if r.roverId == roverId:
            return r.rover_state
    raise HTTPException(
        status_code=404, detail=f'Rover "{roverId}" does not exist')


@app.post("/rovers/connect")
async def connect_to_rover(connection_request: ConnectionRequest):
    print('Connection')

    l.debug(
        f"Received request to /rovers/connect with connection_id={connection_request.connection_id} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")

    request_rover_id = connection_request.rover_id
    request_offer = connection_request.offer

    print(request_rover_id, request_offer)

    # Find if rover is connected to api
    rover = get_rover_by_id(request_rover_id)

    if rover is not None:
        # Request rover to respond to the desired connection string.
        response = await sm.call('connection_offer', data={'offer': request_offer}, to=rover.sid, timeout=20)
        if response is not None:
            l.debug(
                f"Received Response: {response} from Rover {request_rover_id} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")

            return response
        else:
            HTTPException(
                status_code=408, detail="Rover did not respond within allotted connection time.")
    else:
        raise HTTPException(status_code=404, detail="Rover not found")
