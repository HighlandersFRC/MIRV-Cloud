import socketio

HOST = "192.168.1.3"
PORT = 8080

sio = socketio.Client()


@sio.event
def connect():
    print(f"Connected with sid: {sio.sid}")


@sio.event
def disconnect():
    print("Disconnected")


def send(type: str, msg):
    sio.emit(type, msg)


sio.connect(f"http://{HOST}:{PORT}/ws", headers={"roverID": "rover_1"},
            auth={"password": None}, socketio_path="/ws/socket.io")
running = 0
while running < 1000:
    send("data", {"electronics": "degraded"})
    sio.sleep(1)
    running += 1
