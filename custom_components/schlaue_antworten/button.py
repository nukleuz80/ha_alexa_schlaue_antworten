"""Button platform for Schlaue Antworten."""
from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return the device all Schlaue Antworten entities belong to."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="ALEXA - Schlaue Antworten",
        manufacturer="nukleuz80",
        model="Voice AI Bridge",
        sw_version=str(entry.version),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Schlaue Antworten buttons."""
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SchlaueAntwortenStartButton(manager, entry),
            SchlaueAntwortenResetSkillButton(manager, entry),
        ]
    )


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
        self._attr_device_info = _device_info(entry)

    async def async_press(self) -> None:
        """Press button: triggers voice dialog on active Echo."""
        target_echo = self.manager._get_target_echo()
        await self.manager.async_start_dialog(target_echo)


class SchlaueAntwortenResetSkillButton(ButtonEntity):
    """Button entity that replaces the secret address of the own skill."""

    _attr_has_entity_name = True
    _attr_translation_key = "reset_skill"
    _attr_icon = "mdi:link-variant-off"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, manager: Any, entry: ConfigEntry) -> None:
        """Initialize the button."""
        self.manager = manager
        self._attr_unique_id = f"{entry.entry_id}_reset_skill"
        self._attr_device_info = _device_info(entry)

    async def async_press(self) -> None:
        """Press button: new secret address, the skill must be linked again."""
        await self.manager.skill.async_reset()
