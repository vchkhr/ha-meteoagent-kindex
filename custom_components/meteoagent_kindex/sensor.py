"""Platform for sensor integration."""
from __future__ import annotations
import aiohttp
import async_timeout
from bs4 import BeautifulSoup
from datetime import timedelta, datetime, date
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=30)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MeteoAgent K-index sensors."""
    # Check if coordinator exists, otherwise create it
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    if config_entry.entry_id not in hass.data[DOMAIN]:
        coordinator = MeteoAgentCoordinator(hass)
        hass.data[DOMAIN][config_entry.entry_id] = coordinator
    else:
        coordinator = hass.data[DOMAIN][config_entry.entry_id]

    await coordinator.async_config_entry_first_refresh()

    # Create sensors for 20 days
    sensors = []
    for day_offset in range(20):
        sensors.append(KIndexSensor(coordinator, f"day_{day_offset}"))

    async_add_entities(sensors)

class MeteoAgentCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name="MeteoAgent K-index",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        async with async_timeout.timeout(10):
            # Get current date
            today = date.today()

            # Initialize result dictionary
            result = {}

            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.meteoagent.com/widgets/v1/kindex") as resp:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Debug the HTML content
                    _LOGGER.debug(f"Fetched HTML: {html[:10000]}...")  # First 10000 chars for debugging

                    # Process next 20 days
                    for day_offset in range(20):
                        target_date = today + timedelta(days=day_offset)
                        date_format = target_date.strftime("%Y%m%d")

                        # Use the formatted date in the class selector
                        selector = f".date_{date_format} .value__num"
                        element = soup.select_one(selector)

                        # Default value if element not found
                        value = 0

                        if element:
                            try:
                                # Try to convert to integer
                                value = int(element.text.strip())
                                _LOGGER.debug(f"Found K-index for day {day_offset}: {value}")
                            except (ValueError, TypeError):
                                _LOGGER.warning(f"Could not parse K-index value for day {day_offset}: {element.text.strip()}")
                                value = 0
                        else:
                            _LOGGER.warning(f"No K-index element found for day {day_offset}, selector: {selector}")

                        # Store in result with day_X format
                        result[f"day_{day_offset}"] = value

                    if not result:
                        _LOGGER.error("No K-index data found at all")

                    return result

class KIndexSensor(CoordinatorEntity, SensorEntity):
    """Representation of a K-index sensor."""

    def __init__(self, coordinator, sensor_type):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.sensor_type = sensor_type
        day_number = sensor_type.split('_')[1]

        # Get the actual date for this sensor
        target_date = date.today() + timedelta(days=int(day_number))
        date_str = target_date.strftime("%Y-%m-%d")

        if day_number == "0":
            self._attr_name = "MeteoAgent K-index Today"
        elif day_number == "1":
            self._attr_name = "MeteoAgent K-index Tomorrow"
        else:
            self._attr_name = f"MeteoAgent K-index Day {day_number}"

        self._attr_unique_id = f"meteoagent_kindex_{sensor_type}"
        self._attr_native_unit_of_measurement = "K"
        self._attr_state_class = SensorStateClass.MEASUREMENT

        # Add date as attribute
        self._date = date_str

    @property
    def icon(self) -> str:
        """Return the icon based on K-index value."""
        try:
            value = int(self.coordinator.data.get(self.sensor_type, 0))
            if value >= 5:
                return "mdi:head-alert-outline"
            if value >= 4:
                return "mdi:head-snowflake-outline"
            return "mdi:head-heart-outline"
        except (ValueError, TypeError):
            return "mdi:help-circle-outline"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        try:
            return int(self.coordinator.data.get(self.sensor_type, 0))
        except (ValueError, TypeError):
            return 0

    @property
    def extra_state_attributes(self):
        """Return additional sensor attributes."""
        try:
            value = int(self.coordinator.data.get(self.sensor_type, 0))
            severity = self._get_kindex_interpretation(value)
        except (ValueError, TypeError):
            severity = "Unknown"

        return {
            "severity": severity,
            "date": self._date
        }

    def _get_kindex_interpretation(self, value) -> str:
        """Get K-index interpretation."""
        if value is None:
            return "Unknown"
        try:
            value = int(value)
            if value >= 5:
                return "High"
            if value >= 4:
                return "Medium"
            if value >= 1:
                return "Low"
            return "None"
        except (ValueError, TypeError):
            return "Unknown"
