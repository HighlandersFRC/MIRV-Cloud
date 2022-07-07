import socketio
import random
import json

# HOST = "20.221.114.229"
HOST = "192.168.1.5"
PORT = 8080

sio = socketio.Client()


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


@sio.on('disconnect')
def disconnect():
    print('disconnected from server')


def get_scaled_random_number(start, end, scale=1, digits=None):
    return round((random.random() * abs(end - start) + start)*scale, digits)


def send(type: str, msg):
    sio.emit(type, msg)


print(f"http://{HOST}:{PORT}/ws")
sio.connect(f"http://{HOST}:{PORT}/ws", headers={"roverId": "rover_6"},
            auth={"password": None}, socketio_path="/ws/socket.io")
send("data", {
    "roverId": "rover_6",
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

# sio.wait()
# sio.disconnect()
# running = 0
# while running < 1000:
#     send("data", {"electronics": "degraded"})
#     sio.sleep(1)
#     running += 1
