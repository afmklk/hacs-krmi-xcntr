from homeassistant.components.sensor import SensorEntity


class KermiSensor(SensorEntity):
    def __init__(self, coordinator, name, key):
        self.coordinator = coordinator
        self._name = name
        self._key = key

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        data = self.coordinator.data
        return data.get("ResponseData", [])