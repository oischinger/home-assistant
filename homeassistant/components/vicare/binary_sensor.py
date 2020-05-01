"""Viessmann ViCare sensor device."""
import logging

import requests

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_PROBLEM,
)
from homeassistant.const import CONF_DEVICE_CLASS, CONF_NAME
from homeassistant.helpers.entity import Entity

from . import (
    DOMAIN as VICARE_DOMAIN,
    VICARE_API,
    VICARE_HEATING_TYPE,
    VICARE_NAME,
    HeatingType,
)

_LOGGER = logging.getLogger(__name__)

CONF_GETTER = "getter"

SENSOR_CIRCULATION_PUMP_ACTIVE = "circulationpump_active"
SENSOR_BURNER_ACTIVE = "circulationpump_active"
SENSOR_ACTIVE_ERROR = "active_error"
SENSOR_COMPRESSOR_ACTIVE = "compressor_active"

SENSOR_TYPES = {
    SENSOR_CIRCULATION_PUMP_ACTIVE: {
        CONF_NAME: "Circulation pump active",
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
        CONF_GETTER: lambda api: api.getCirculationPumpActive(),
    },
    SENSOR_ACTIVE_ERROR: {
        CONF_NAME: "Active error",
        CONF_DEVICE_CLASS: DEVICE_CLASS_PROBLEM,
        CONF_GETTER: lambda api: api.getActiveError(),
    },
    SENSOR_BURNER_ACTIVE: {
        CONF_NAME: "Burner active",
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
        CONF_GETTER: lambda api: api.getBurnerActive(),
    },
    SENSOR_COMPRESSOR_ACTIVE: {
        CONF_NAME: "Compressor active",
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
        CONF_GETTER: lambda api: api.getCompressorActive(),
    },
}

SENSORS_GENERIC = [SENSOR_CIRCULATION_PUMP_ACTIVE, SENSOR_ACTIVE_ERROR]

SENSORS_BY_HEATINGTYPE = {
    HeatingType.gas: [
        SENSOR_BURNER_ACTIVE
    ],  # add additional gas sensors (consumption, etc.)
    HeatingType.heatpump: [SENSOR_COMPRESSOR_ACTIVE],
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Create the ViCare sensor devices."""
    if discovery_info is None:
        return

    vicare_api = hass.data[VICARE_DOMAIN][VICARE_API]
    heating_type = hass.data[VICARE_DOMAIN][VICARE_HEATING_TYPE]

    sensors = SENSORS_GENERIC

    if heating_type != HeatingType.generic:
        sensors.extend(SENSORS_BY_HEATINGTYPE[heating_type])

    add_entities(
        [
            ViCareBinarySensor(
                hass.data[VICARE_DOMAIN][VICARE_NAME], vicare_api, sensor
            )
            for sensor in sensors
        ]
    )


class ViCareBinarySensor(Entity):
    """Representation of a ViCare sensor."""

    def __init__(self, name, api, sensortype):
        """Initialize the sensor."""
        self._sensor = SENSOR_TYPES[sensortype]
        self._name = f"{name} {self._sensor[CONF_NAME]}"
        self._api = api
        self._sensortype = sensortype
        self._state = None

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._api.service.id}-{self._sensortype}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self._sensor[CONF_DEVICE_CLASS]

    def update(self):
        """Update state of sensor."""
        try:
            self._state = self._sensor[CONF_GETTER](self._api)
        except requests.exceptions.ConnectionError:
            _LOGGER.error("Unable to retrieve data from ViCare server")
        except ValueError:
            _LOGGER.error("Unable to decode data from ViCare server")
