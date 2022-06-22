HEALTH_STATES = ["unhealthy", "degraded", "healthy", "unavailable"]
ROVER_STATES = ["docked", "remoteOperation", "disabled", "eStop"]
ROVER_STATUSES = ["available", "unavailable"]
ROVER_LOCATION = [-104.969523, 40.474083]

class Rover:

    def __init__(self, rid: str, sid: str):
        self.roverID = rid
        self.sid = sid
        self.rover_state = {
            "roverID": self.roverID,
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
                "long": ROVER_LOCATION[0],
                "lat": ROVER_LOCATION[1],
                "heading": 90,
                "speed": 0
            }
        }
    
    def update(self, data):
        if data:
            for data_key in data:
                for rover_key in self.rover_state:
                    if data_key == rover_key and not isinstance(self.rover_state[rover_key], dict):
                        self.rover_state[rover_key] = data[rover_key]
                for health_key in self.rover_state["health"]:
                    if data_key == health_key:
                        self.rover_state["health"][health_key] = data[data_key]
                for tel_key in self.rover_state["telemetry"]:
                    if data_key == tel_key:
                        self.rover_state["telemetry"][tel_key] = data[data_key]

    def getGeneral(self):
        return {
            "roverID": self.rover_state["roverID"],
            "state": self.rover_state["state"],
            "status": self.rover_state["status"],
            "battery-voltage": self.rover_state["battery-voltage"]
        }