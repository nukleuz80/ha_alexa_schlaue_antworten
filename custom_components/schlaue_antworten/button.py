"""Button platform for Schlaue Antworten."""
from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
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
    """Set up the Schlaue Antworten button."""
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SchlaueAntwortenStartButton(manager, entry)])


class SchlaueAntwortenStartButton(ButtonEntity):
    """Button entity that triggers the Schlaue Antworten voice dialog."""

    _attr_has_entity_name = True
    _attr_translation_key = "start_dialog"
    _attr_icon = "mdi:microphone-message"

    def __init__(self, manager: Any, entry: ConfigEntry) -> None:
        """Initialize the button."""
        self.manager = manager
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_start_button"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="ALEXA - Schlaue Antworten",
            manufacturer="nukleuz80",
            model="Voice AI Bridge",
            sw_version=str(entry.version),
        )

    async def async_press(self) -> None:
        """Press button: triggers voice dialog on active Echo."""
        target_echo = self.manager._get_target_echo()
        await self.manager.async_start_dialog(target_echo)
