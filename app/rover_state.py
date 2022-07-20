HEALTH_STATES = ["unhealthy", "degraded", "healthy", "unavailable"]
ROVER_STATES = ["disconnected", "disconnected_fault", "e_stop", "connected_disabled",
                "connected_idle_roaming", "connected_idle_docked", "connected_fault", "autonomous", "remote_operation"]
ROVER_STATUSES = ["available", "unavailable"]
ROVER_LOCATION = [-104.969523, 40.474083]


class Rover:

    def __init__(self, rid: str, sid: str):
        self.rover_id = rid
        self.sid = sid
        self.rover_state = {
            "rover_id": self.rover_id,
            "state": ROVER_STATES[0],
            "status": ROVER_STATUSES[0],
            "battery_percent": 100,
            "battery_voltage": 14,
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

    # data: {"battery-voltage": "12"}
    # data: {"health/electronics": "degraded"}
    def update_individual(self, data):
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

    def update(self, new_rover_state):
        self.rover_state = new_rover_state
        return self

    def getGeneral(self):
        return {
            "rover_id": self.rover_state["rover_id"],
            "state": self.rover_state["state"],
            "status": self.rover_state["status"],
            "battery_voltage": self.rover_state["battery_voltage"]
        }

    def getState(self):
        return self.rover_state
