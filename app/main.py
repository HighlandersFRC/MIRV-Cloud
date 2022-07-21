from http.client import HTTPException
import datetime
from typing import Union, List
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
import os
import sys
import logging
from keycloak import KeycloakOpenID

from socket_manager import MirvSocketManager
from auth import MirvKeycloakProvider


ISO_8601_FORMAT_STRING = "%Y-%m-%dT%H:%M:%SZ"

KEYCLOAK_ENDPOINT = os.getenv("KEYCLOAK_ENDPOINT")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM")
KEYCLOAK_CLIENT_USERS = os.getenv("KEYCLOAK_CLIENT_USERS")
KEYCLOAK_CLIENT_DEVICES = os.getenv("KEYCLOAK_CLIENT_DEVICES")
KEYCLOAK_SECRET_KEY = os.getenv("KEYCLOAK_SECRET_KEY")

logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | {level} | <level>{message}</level>",
)

app = FastAPI()
keycloakClient = MirvKeycloakProvider(
    KEYCLOAK_ENDPOINT,
    KEYCLOAK_REALM,
    KEYCLOAK_CLIENT_USERS,
    KEYCLOAK_CLIENT_DEVICES,
    KEYCLOAK_SECRET_KEY,
)
socketManager = MirvSocketManager(app, keycloakClient)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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


class GarageCommand(BaseModel):
    connection_id: str
    garage_id: str
    cmd: dict


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


def get_rover_by_id(rover_id):
    for rover in socketManager.rovers:
        if rover.rover_id == rover_id:
            return rover
    return None


def get_garage_by_id(garage_id):
    for garage in socketManager.garages:
        if garage.garage_id == garage_id:
            return garage
    return None


def verify_access_token_user(access_token: str = Depends(oauth2_scheme)):
    if keycloakClient.validate_token_user(access_token):
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_access_token_device(access_token: str = Depends(oauth2_scheme)):
    if keycloakClient.validate_token_device(access_token):
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


##################################################################
# Rest Endpoint
##################################################################
@app.get("/")
def read_root():
    logger.info("/")
    logger.debug(
        f"Received request to / at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
    return {"Hello": "World"}


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    print(form_data.username, form_data.password)
    access_token = keycloakClient.get_access_token_device(
        form_data.username, form_data.password)
    if not access_token:
        logger.debug(
            f"Rejected Request for access token from {form_data.username}. Incorrect Username or Password {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not keycloakClient.get_user_info_device(access_token['access_token']):
        logger.debug(
            f"Rejected Request for access token from {form_data.username} {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return access_token


# GET: list of rovers and statuses
@app.get("/rovers")
async def read_item(token_valid: bool = Depends(verify_access_token_user)):
    logger.info("/rovers")
    logger.debug(
        f"Received request to /rovers at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
    return [r.getState() for r in socketManager.rovers]


@app.get("/garages")
async def read_item(q: Union[str, None] = None):
    logger.debug(
        f"Received request to /garages at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
    return [g.getState() for g in socketManager.garages]


@app.get("/rovers/{rover_id}")
async def read_item(rover_id: str, token_valid: bool = Depends(verify_access_token_user)):
    logger.info(f"/rovers/{rover_id}")
    logger.debug(
        f"Received request to /rovers/{{rover_id}} with rover_id={rover_id} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
    for r in socketManager.ROVERS:
        if r.rover_id == rover_id:
            return r.rover_state
    raise HTTPException(
        status_code=404,
        detail=f'Rover "{rover_id}" does not exist',
    )


@app.post("/rovers/connect")
async def connect_to_rover(connection_request: ConnectionRequest, token_valid: bool = Depends(verify_access_token_user)):
    logger.info("/rovers/connect")
    logger.debug(
        f"Received request to /rovers/connect with connection_id={connection_request.connection_id} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")

    request_rover_id = connection_request.rover_id
    request_offer = connection_request.offer

    # Find if rover is connected to api
    rover = get_rover_by_id(request_rover_id)

    if rover is not None:
        # Request rover to respond to the desired connection string.
        response = await socketManager.sm.call('connection_offer', data={'offer': request_offer}, to=rover.sid, timeout=20)
        if response is not None:
            logger.debug(
                f"Received Response: {response} from Rover {request_rover_id} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
            return response
        else:
            raise HTTPException(
                status_code=408,
                detail="Rover did not respond within allotted connection time.",
            )
    else:
        raise HTTPException(
            status_code=404,
            detail="Rover not found",
        )


@app.post("/garages/cmd")
async def send_garage_command(garage_cmd: GarageCommand, token_valid: bool = Depends(verify_access_token_user)):

    logger.debug(
        f"Received request to /rovers/connect with connection_id={garage_cmd.connection_id} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")

    request_garage_id = garage_cmd.garage_id
    request_cmd = garage_cmd.cmd

    garage = get_garage_by_id(request_garage_id)
    if garage is not None:
        response = await socketManager.sm.call('connection_offer', data={'cmd': request_cmd}, to=garage.sid, timeout=20)
        if response is not None:
            logger.debug(
                f"Received Response: {response} from Garage {request_garage_id} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
            return response
        else:
            raise HTTPException(
                status_code=408,
                detail="Garage did not respond within allotted connection time.",
            )
    return 200
