class DroneAdapter:
    def send_target(self, x, y):
        return {"status":"SIMULATED","target":{"x":x,"y":y}}
