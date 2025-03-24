"""Platform for sensor integration."""
from __future__ import annotations
import aiohttp
import async_timeout
from bs4 import BeautifulSoup
from datetime import timedelta
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

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=30)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MeteoAgent K-index sensors."""
    coordinator = MeteoAgentCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([
        KIndexSensor(coordinator, "today"),
        KIndexSensor(coordinator, "tomorrow")
    ])

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
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.meteoagent.com/widgets/v1/kindex") as resp:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    today = soup.select_one('.widget-kindex__forecast_one .meta__value strong').text.strip()
                    tomorrow = soup.select_one('.widget-kindex__forecast_two .meta__value strong').text.strip()

                    return {
                        "today": int(today.split()[1]),
                        "tomorrow": int(tomorrow.split()[1])
                    }

class KIndexSensor(CoordinatorEntity, SensorEntity):
    """Representation of a K-index sensor."""

    def __init__(self, coordinator, sensor_type):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.sensor_type = sensor_type
        self._attr_name = f"MeteoAgent K-index for {sensor_type.title()}"
        self._attr_unique_id = f"meteoagent_kindex_{sensor_type}"
        self._attr_native_unit_of_measurement = "K"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def icon(self) -> str:
        """Return the icon based on K-index value."""
        value = self.coordinator.data[self.sensor_type]
        if value >= 5:
            return "mdi:head-alert-outline"
        if value >= 4:
            return "mdi:head-snowflake-outline"
        return "mdi:head-heart-outline"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.coordinator.data[self.sensor_type]

    @property
    def extra_state_attributes(self):
        """Return additional sensor attributes."""
        value = self.coordinator.data[self.sensor_type]
        severity = self._get_kindex_interpretation(value)

        return {
            "severity": severity
        }

    def _get_kindex_interpretation(self, value: int) -> str:
        """Get K-index interpretation."""
        if value >= 5:
            return "High"
        if value >= 4:
            return "Medium"
        if value >= 1:
            return "Low"
        return "None"
