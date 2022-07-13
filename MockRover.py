import socketio
import json
import asyncio
import logging
import uuid
from aiohttp import web
import cv2
from av import VideoFrame
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
import requests
import numpy
import math
import random
import time
import schedule
import threading

CLOUD_HOST = "52.185.79.181"
CLOUD_PORT = 8080

HEALTH_STATES = ["unhealthy", "degraded", "healthy", "unavailable"]
ROVER_STATES = ["docked", "remoteOperation", "disabled", "eStop"]
ROVER_STATUSES = ["available", "unavailable"]
ROVER_LOCATION = [-104.969523, 40.474083]

ROVER_ID = "rover_42"
SEND_INTERVAL_SECONDS = 30

USERNAME = "rover_dev"
PASSWORD = "rover_dev"


# Setup webtrc connection components
logger = logging.getLogger("pc")
pcs = set()

# Setup OpenCV Capture Components
# TODO replace with stream read from camera topic

# Setup Socket Connection with the cloud
sio = socketio.Client()


# Class Describing how to send VideoStreams to the Cloud
class FlagVideoStreamTrack(VideoStreamTrack):
    """
    A video track that returns an animated flag.
    """

    def __init__(self):
        super().__init__()  # don't forget this!
        self.counter = 0
        height, width = 480, 640

        # generate flag
        data_bgr = numpy.hstack(
            [
                self._create_rectangle(
                    width=213, height=480, color=(255, 0, 0)
                ),  # blue
                self._create_rectangle(
                    width=214, height=480, color=(255, 255, 255)
                ),  # white
                self._create_rectangle(
                    width=213, height=480, color=(0, 0, 255)),  # red
            ]
        )

        # shrink and center it
        M = numpy.float32([[0.5, 0, width / 4], [0, 0.5, height / 4]])
        data_bgr = cv2.warpAffine(data_bgr, M, (width, height))

        # compute animation
        omega = 2 * math.pi / height
        id_x = numpy.tile(numpy.array(
            range(width), dtype=numpy.float32), (height, 1))
        id_y = numpy.tile(
            numpy.array(range(height), dtype=numpy.float32), (width, 1)
        ).transpose()

        self.frames = []
        for k in range(30):
            phase = 2 * k * math.pi / 30
            map_x = id_x + 10 * numpy.cos(omega * id_x + phase)
            map_y = id_y + 10 * numpy.sin(omega * id_x + phase)
            self.frames.append(
                VideoFrame.from_ndarray(
                    cv2.remap(data_bgr, map_x, map_y, cv2.INTER_LINEAR), format="bgr24"
                )
            )

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        frame = self.frames[self.counter % 30]
        frame.pts = pts
        frame.time_base = time_base
        self.counter += 1
        return frame

    def _create_rectangle(self, width, height, color):
        data_bgr = numpy.zeros((height, width, 3), numpy.uint8)
        data_bgr[:, :] = color
        return data_bgr

# Website posts an offer to python server


def get_scaled_random_number(start, end, scale=1, digits=None):
    return round((random.random() * abs(end - start) + start)*scale, digits)


async def offer(request):
    params = await request.json()
    print("Received Params")
    print(params)
    offer = RTCSessionDescription(
        sdp=params["offer"]["sdp"], type=params["offer"]["type"])

    pc = RTCPeerConnection()
    pc.addTrack(FlagVideoStreamTrack())
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs.add(pc)

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            print("Received: ", message)
            if message == "send_data":
                sendRoverData()
            elif message == "send_markers":
                sendMarkerData()

        data_channel = channel

        def sendRoverData():
            print("Sending data")
            data_channel.send(json.dumps({
                "roverId": ROVER_ID,
                "state": ROVER_STATES[0],
                "status": ROVER_STATUSES[0],
                "battery": random.randint(0, 100),
                "health": {
                    "encoder": HEALTH_STATES[random.randint(0, 3)],
                    "mechanical": HEALTH_STATES[random.randint(0, 3)],
                    "lidar": HEALTH_STATES[random.randint(0, 3)],
                    "camera": HEALTH_STATES[random.randint(0, 3)],
                    "imu": HEALTH_STATES[random.randint(0, 3)],
                    "gps": HEALTH_STATES[random.randint(0, 3)],
                    "garage": HEALTH_STATES[random.randint(0, 3)],
                },
                "telemetry": {
                    "location": {
                        "long": ROVER_LOCATION[0] + get_scaled_random_number(-1, 1, scale=0.001, digits=6),
                        "lat": ROVER_LOCATION[1] + get_scaled_random_number(-1, 1, scale=0.001, digits=6)
                    },
                    "heading": get_scaled_random_number(0, 360, digits=2),
                    "speed": get_scaled_random_number(0, 20, digits=2),
                }
            }))

        def sendMarkerData():
            print("Sending data")
            data_channel.send(json.dumps([
                {
                    'id': "pi_lit_1",
                    "description": "Pi lit 1",
                    'location': {
                        "long": ROVER_LOCATION[0] + get_scaled_random_number(-1, 1, scale=0.001, digits=6),
                        "lat": ROVER_LOCATION[1] + get_scaled_random_number(-1, 1, scale=0.001, digits=6)
                    }
                },
                {
                    'id': "pi_lit_2",
                    "description": "Pi lit 2",
                    'location': {
                        "long": ROVER_LOCATION[0] + get_scaled_random_number(-1, 1, scale=0.001, digits=6),
                        "lat": ROVER_LOCATION[1] + get_scaled_random_number(-1, 1, scale=0.001, digits=6)
                    }
                }
            ]))

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        #log_info("Connection state is %s", pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    # handle offer
    await pc.setRemoteDescription(offer)

    # send answer
    answer = await pc.createAnswer()
    print(answer)
    await pc.setLocalDescription(answer)
    print("Returning Answer")
    print(json.dumps({"sdp": pc.localDescription.sdp,
          "type": pc.localDescription.type}))

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"answer": json.dumps(
                {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})}
        ),
    )


async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


@sio.on('connect')
def connect():
    print('connection established')


@sio.on('message')
def message(data):
    print('message received with ', data)
    # sio.emit('my response', {'response': 'my response'})


@sio.on('exception')
def exception(data):
    print('exception received with ', data)
    # sio.emit('my response', {'response': 'my response'})


@sio.on('connection_offer')
def connection_offer(data):
    # I was able to get the WebRTC offer / answer exchange working through asyncio. However, despite valid signals being returned to the client. It was unable to form a valid connection
    # There appears to be a bug in the aiortc implementation that prevents this from working without either the aiortc signaling server, or an http server.
    # Long story short. A local http server is being used to relay the signal.
    x = requests.post('http://localhost:8000/offer', json=data)
    return x.json()


@sio.on('disconnect')
def disconnect():
    print('disconnected from server')


def send(type: str, msg):
    sio.emit(type, msg)


def on_shutdown():
    # close peer connections
    coros = [pc.close() for pc in pcs]
    asyncio.gather(*coros)
    pcs.clear()
    sio.disconnect()



# Send sample Rover Status to Cloud
print(f"http://{CLOUD_HOST}:{CLOUD_PORT}/ws")
sio.connect(f"ws://{CLOUD_HOST}:{CLOUD_PORT}/ws", headers={"roverId": ROVER_ID},
            auth={"token": "PASSWORD"}, socketio_path="/ws/socket.io")
send("data", {
    "roverId": ROVER_ID,
    "state": "docked",
    "status": "available",
    "battery-percent": 12,
    "battery-voltage": 18,
    "health": {
        "electronics": "healthy",
        "drivetrain": "healthy",
        "intake": "healthy",
        "sensors": "healthy",
        "garage": "healthy",
        "power": "healthy",
        "general": "healthy"
    },
    "telemetry": {
        "location": {
            "lat": 39,
            "long": -105
        },
        "heading": 90,
        "speed": 0
    }
})

app = web.Application()
app.on_shutdown.append(on_shutdown)
app.router.add_post("/offer", offer)

web.run_app(
    app, access_log=None, host="0.0.0.0", port=8000
)
