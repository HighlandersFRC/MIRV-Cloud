HEALTH_STATES = ["unhealthy", "degraded", "healthy", "unavailable"]
GARAGE_STATES = ["retracted", "deployed", "disabled", "unavailable", "locked"]
GARAGE_STATUSES = ["available", "unavailable"]


class Garage:
    def __init__(self, gid: str, sid: str):
        self.garage_id = gid
        self.sid = sid
        self.garage_state = {
            "garageId": self.garage_id,
            "state": GARAGE_STATES[0],
            "status": GARAGE_STATUSES[0],
            "health": {
                "electronics": HEALTH_STATES[2],
                "actuators": HEALTH_STATES[2],
                "lights": HEALTH_STATES[2],
                "power": HEALTH_STATES[2],
                "general": HEALTH_STATES[2]
            },
        }

    # data: {"battery-voltage": "12"}
    # data: {"health/electronics": "degraded"}
    def update_individual(self, data):
        if data:
            for data_key in data:
                for GARAGE_key in self.GARAGE_state:
                    if data_key == GARAGE_key and not isinstance(self.GARAGE_state[GARAGE_key], dict):
                        self.GARAGE_state[GARAGE_key] = data[GARAGE_key]
                for health_key in self.GARAGE_state["health"]:
                    if data_key == health_key:
                        self.GARAGE_state["health"][health_key] = data[data_key]
                        
    def update(self, new_GARAGE_state):
        self.GARAGE_state = new_GARAGE_state
        return self

    def getGeneral(self):
        return {
            "garageId": self.GARAGE_state["garage_id"],
            "state": self.GARAGE_state["state"],
            "status": self.GARAGE_state["status"],
        }

    def getState(self):
        return self.GARAGE_state
