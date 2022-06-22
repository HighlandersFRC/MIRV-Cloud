from hashlib import sha256
from http.client import HTTPException
import random
import datetime
from typing import Union, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_socketio import SocketManager
from pydantic import BaseModel
import uvicorn
from roverstate import Rover
import os

ROVERS = []

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
# HOST = os.getenv("HOST")
# PORT = os.getenv("PORT")

# HOST = "192.168.1.3"
PORT = 80


@sm.on('connect')
def handle_connect(sid, environ, auth):
    ROVERS.append(Rover(environ["HTTP_ROVERID"], sid))
    if auth["password"] != PASS:
        raise ConnectionRefusedError("Authentication failed")
    print(f"Connected sid: {sid}")
    print(f"{len(ROVERS)} Rover(s) connected")


@sm.on('data')
def handle_data(sid, data):
    print(f"Received {data} from sid: {sid}")
    for r in ROVERS:
        if r.sid == sid:
            r.update(data)
            break


@sm.on('disconnect')
def handle_disconnect(sid):
    for i in range(len(ROVERS)):
        if ROVERS[i].sid == sid:
            ROVERS.pop(i)
            break
    print(f"Disconnected sid: {sid}")


HEALTH_STATES = ["unhealthy", "degraded", "healthy", "unavailable"]
ROVER_STATES = ["docked", "remoteOperation", "disabled", "eStop"]
ROVER_STATUSES = ["available", "unavailable"]
ROVER_LOCATION = [-104.969523, 40.474083]


class ConnectionRequest(BaseModel):
    connection_id: str
    rover_id: str
    offer: str


class ConnectionResponseValid(BaseModel):
    connection_id: str
    answer: str
    candidate: str


def get_scaled_random_number(start, end, scale=1, digits=None):
    return round((random.random() * abs(end - start) + start)*scale, digits)


@app.get("/")
def read_root():
    return {"Hello": "World"}


# GET: list of rovers and statuses
@app.get("/rovers")
def read_item(q: Union[str, None] = None):
    return [r.getGeneral() for r in ROVERS]


@app.get("/rovers/{roverID}")
def read_item(roverID: str, q: Union[str, None] = None):
    for r in ROVERS:
        if r.roverID == roverID:
            return r.rover_state
    raise HTTPException(
        status_code=404, detail=f'Rover "{roverID}" does not exist')


@app.post("/rovers/connect")
def connect_to_rover(connection_request: ConnectionRequest):
    resp = ConnectionResponseValid()
    resp.connection_id = connection_request.connection_id
    resp.answer = f'answer_{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}'
    resp.candidate = f'candidate_{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}'
    return resp


# PUT: Add/update rover status info?


# POST: Send command?

# if __name__ == "__main__":
#     uvicorn.run(app, port=PORT)  # , host=HOST
