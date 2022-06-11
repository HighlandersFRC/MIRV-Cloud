import random
import datetime
from typing import Union
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return [
        {
            "roverId": "rover_1",
            "state": ROVER_STATES[0],
            "status": ROVER_STATUSES[0],
            "battery": random.randint(0, 100)
        },
        {
            "roverId": "rover_2",
            "state": ROVER_STATES[random.randint(0, 3)],
            "status": ROVER_STATUSES[random.randint(0, 1)],
            "battery": random.randint(0, 100)
        },
    ]


@app.get("/rovers/{roverId}")
def read_item(roverId: str, q: Union[str, None] = None):
    return {
        "roverId": roverId,
        "state": ROVER_STATES[0],
        "status": ROVER_STATUSES[0],
        "battery": random.randint(0, 100),
        "health": {
            "electronics": HEALTH_STATES[random.randint(0, 3)],
            "drivetrain": HEALTH_STATES[random.randint(0, 3)],
            "intake": HEALTH_STATES[random.randint(0, 3)],
            "sensors": HEALTH_STATES[random.randint(0, 3)],
            "garage": HEALTH_STATES[random.randint(0, 3)],
            "power": HEALTH_STATES[random.randint(0, 3)],
            "general": HEALTH_STATES[random.randint(0, 3)],
        },
        "telemetry": {
            "location": {
                "long": ROVER_LOCATION[0] + get_scaled_random_number(-1, 1, scale=0.0001, digits=6),
                "lat": ROVER_LOCATION[1] + get_scaled_random_number(-1, 1, scale=0.0001, digits=6)
            },
            "heading": get_scaled_random_number(0, 360, digits=2),
            "speed": get_scaled_random_number(0, 20, digits=2),
        }
    }


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
#     uvicorn.run(app, host="0.0.0.0", port=int(os.getenv('APP_PORT')))
