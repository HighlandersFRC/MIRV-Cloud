import socketio
import eventlet
from eventlet import wsgi

HEALTH_STATES = ["unhealthy", "degraded", "healthy", "unavailable"]
ROVER_STATES = ["docked", "remoteOperation", "disabled", "eStop"]
ROVER_STATUSES = ["available", "unavailable"]
ROVER_LOCATION = [-104.969523, 40.474083]

class Rover:
    def __init__(self, id: str):
        self.sio = socketio.Server()
        self.app = socketio.WSGIApp(self.sio)
        self.start()
        self.roverID = id
        self.rover_state = {
            "roverID": id,
            "state": ROVER_STATES[0],
            "status": ROVER_STATUSES[0],
            "battery-percent": 100,
            "battery-voltage": 14,
            "health": {
                "electronics": HEALTH_STATES[2],
                "drivetrain": HEALTH_STATES[2],
                "intake": HEALTH_STATES[2],
                "sensors": HEALTH_STATES[2],
                "garage": HEALTH_STATES[2],
                "power": HEALTH_STATES[2],
                "general": HEALTH_STATES[2]
            },
            "telemetry": {
                "location": {
                    "long": ROVER_LOCATION[0],
                    "lat": ROVER_LOCATION[1]
                },
                "heading": 90,
                "speed": 0
            }
        }

    
    def connect(self, sid):
        print(f"Connected to sid: {sid}")
        return True
    
    
    def data(self, data):
        if data != None:
            for data_key in data:
                for rover_key in self.rover_state:
                    if data_key == rover_key:
                        self.rover_state[rover_key] = data[rover_key]

    
    def disconnect(self, sid):
        print(f"Disconnected sid: {sid}")

    def start(self):
        wsgi.server(eventlet.listen(("172.250.250.76", 7070)), self.app)

    def getID(self):
        return self.roverID

    def getFull(self):
        return self.rover_state

    def getGeneral(self):
        return {
            "roverID": self.rover_state["roverID"],
            "state": self.rover_state["state"],
            "status": self.rover_state["status"],
            "battery-voltage": self.rover_state["battery-voltage"]
        }