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

ISO_8601_FORMAT_STRING = "%Y-%m-%dT%H:%M:%SZ"

PASS = os.getenv("PASSWORD")
KEYCLOAK_ENDPOINT = os.getenv("KEYCLOAK_ENDPOINT")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM")
KEYCLOAK_CLIENT = os.getenv("KEYCLOAK_CLIENT")
KEYCLOAK_SECRET_KEY = os.getenv("KEYCLOAK_SECRET_KEY")

keycloak_openid = KeycloakOpenID(server_url=f"{KEYCLOAK_ENDPOINT}/auth/",
                                 client_id=KEYCLOAK_CLIENT,
                                 realm_name=KEYCLOAK_REALM,
                                 client_secret_key=KEYCLOAK_SECRET_KEY)

# Set Logging Object and Functionality
# logging.basicConfig(
#     format='%(levelname)-8s [%(asctime)s|%(filename)s:%(lineno)d] %(message)s',
#     datefmt=ISO_8601_FORMAT_STRING,
#     level=logging.DEBUG,
# )
# logger = logging.getLogger(__name__)
logger.add(sys.stdout, colorize=True,
           format="<green>{time:HH:mm:ss}</green> | {level} | <level>{message}</level>")

app = FastAPI()
mirvSocketManager = MirvSocketManager(app, PASS)
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


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


def get_rover_by_id(rover_id):
    for rover in mirvSocketManager.ROVERS:
        if rover.roverId == rover_id:
            return rover
    return None


def get_access_token(username: str, password: str):
    try:
        return keycloak_openid.token(username, password)
    except:
        return None


def get_user_info(token):
    try:
        return keycloak_openid.userinfo(token)
    except:
        return False


def validate_token(token):
    if not get_user_info(token):
        return False
    return True


def get_current_token(access_token: str = Depends(oauth2_scheme)):
    validate_token = get_user_info(access_token)
    logger.info(access_token)
    logger.info(validate_token)
    if validate_token:
        return True
    else:
        logger.error(f"Invalid Access Token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=validate_token,
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
    access_token = get_access_token(form_data.username, form_data.password)
    logger.info("/token")
    logger.info(access_token)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not get_user_info(access_token['access_token']):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return access_token


# GET: list of rovers and statuses
@app.get("/rovers")
async def read_item(token_valid: bool = Depends(get_current_token)):
    logger.info("/rovers")
    logger.debug(
        f"Received request to /rovers at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
    return [r.getState() for r in mirvSocketManager.ROVERS]


@app.get("/rovers/{roverId}")
async def read_item(roverId: str, token_valid: bool = Depends(get_current_token)):
    logger.info(f"/rovers/{roverId}")
    logger.debug(
        f"Received request to /rovers/{{roverId}} with roverId={roverId} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")
    for r in mirvSocketManager.ROVERS:
        if r.roverId == roverId:
            return r.rover_state
    raise HTTPException(
        status_code=404, detail=f'Rover "{roverId}" does not exist')


@app.post("/rovers/connect")
async def connect_to_rover(connection_request: ConnectionRequest, token_valid: bool = Depends(get_current_token)):
    logger.info("/rovers/connect")
    print('Connection')

    logger.debug(
        f"Received request to /rovers/connect with connection_id={connection_request.connection_id} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")

    request_rover_id = connection_request.rover_id
    request_offer = connection_request.offer

    print(request_rover_id, request_offer)

    # Find if rover is connected to api
    rover = get_rover_by_id(request_rover_id)

    if rover is not None:
        # Request rover to respond to the desired connection string.
        response = await mirvSocketManager.sm.call('connection_offer', data={'offer': request_offer}, to=rover.sid, timeout=20)
        if response is not None:
            logger.debug(
                f"Received Response: {response} from Rover {request_rover_id} at {datetime.datetime.utcnow().strftime(ISO_8601_FORMAT_STRING)}")

            return response
        else:
            HTTPException(
                status_code=408, detail="Rover did not respond within allotted connection time.")
    else:
        raise HTTPException(status_code=404, detail="Rover not found")



