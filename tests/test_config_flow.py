"""Tests for the config and options flow."""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.schlaue_antworten.const import DOMAIN

from .conftest import SetupEntry


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    """The setup asks nothing and stores the default options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"]["primary_agent"]


async def test_single_instance(hass: HomeAssistant, setup_entry: SetupEntry) -> None:
    """A second entry is refused."""
    await setup_entry()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT


async def test_options_menu(hass: HomeAssistant, setup_entry: SetupEntry) -> None:
    """The options start with the menu of settings and history."""
    entry = await setup_entry()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert set(result["menu_options"]) == {"settings", "history"}
