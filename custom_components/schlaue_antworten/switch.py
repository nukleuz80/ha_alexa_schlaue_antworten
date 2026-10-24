"""Switch platform for Schlaue Antworten."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Schlaue Antworten switch."""
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SchlaueAntwortenTriggerSwitch(manager, entry)])


class SchlaueAntwortenTriggerSwitch(SwitchEntity):
    """Switch entity that triggers the Schlaue Antworten voice dialog."""

    _attr_has_entity_name = True
    _attr_translation_key = "dialog_trigger"
    _attr_icon = "mdi:forum"

    def __init__(self, manager: Any, entry: ConfigEntry) -> None:
        """Initialize the switch."""
        self.manager = manager
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_dialog_trigger"
        self._attr_is_on = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="ALEXA - Schlaue Antworten",
            manufacturer="nukleuz80",
            model="Voice AI Bridge",
            sw_version=str(entry.version),
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on switch: triggers voice dialog on active Echo and resets to off."""
        self._attr_is_on = True
        self.async_write_ha_state()

        target_echo = self.manager._get_target_echo()
        await self.manager.async_start_dialog(target_echo)

        # Automatically reset back to off (momentary switch behavior)
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off switch (no-op, automatically off)."""
        self._attr_is_on = False
        self.async_write_ha_state()
