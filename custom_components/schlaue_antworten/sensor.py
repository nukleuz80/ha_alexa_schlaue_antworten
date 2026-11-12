"""Sensor platform for Schlaue Antworten."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Schlaue Antworten sensor platform."""
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SchlaueAntwortenQueriesTodaySensor(manager, entry)])


class SchlaueAntwortenQueriesTodaySensor(SensorEntity):
    """Statistical sensor counting AI queries today."""

    _attr_has_entity_name = True
    _attr_translation_key = "queries_today"
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "Anfragen"

    def __init__(self, manager: Any, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.manager = manager
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_queries_today"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="ALEXA - Schlaue Antworten",
            manufacturer="nukleuz80",
            model="Voice AI Bridge",
            sw_version=str(entry.version),
        )

    async def async_added_to_hass(self) -> None:
        """Register listener when added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.manager.register_stats_listener(self.async_write_ha_state)
        )

    @property
    def native_value(self) -> int:
        """Return the number of queries today."""
        self.manager._check_date_rollover()
        return int(self.manager.stats.get("today_count", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return statistical details as extra attributes."""
        stats = self.manager.stats
        means = self.manager.timing_summary()
        return {
            "anfragen_heute": stats.get("today_count", 0),
            "kurze_antworten_heute": stats.get("today_short", 0),
            "ausfuehrliche_antworten_heute": stats.get("today_detailed", 0),
            "anfragen_gesamt": stats.get("total_count", 0),
            "letzte_anfrage": stats.get("last_query"),
            "letztes_echo": stats.get("last_device"),
            "letzte_uhrzeit": stats.get("last_time"),
            "letzte_dauer_sekunden": stats.get("last_duration"),
            "letzte_ki_dauer_sekunden": stats.get("last_llm_seconds"),
            "letzter_agent": stats.get("last_agent"),
            "letzter_weg": stats.get("last_path"),
            "mittlere_ki_dauer_sekunden": means["llm"],
            "mittlere_gesamtdauer_sekunden": means["total"],
            "gemessene_anfragen": len(stats.get("recent") or []),
            "datum": stats.get("date"),
            "letzte_skill_anfrage": self.manager.skill.last_skill_request,
        }

