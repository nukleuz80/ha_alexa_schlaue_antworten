"""Tests for finding the push target that reaches the phone."""
from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.data_entry_flow import FlowResultType

from custom_components.schlaue_antworten.const import DOMAIN

from .conftest import ECHO, SetupEntry


def _phone(hass: HomeAssistant, name: str = "mobile_app_iphone") -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    async def _record(call: ServiceCall) -> None:
        calls.append(dict(call.data))

    hass.services.async_register("notify", name, _record)
    return calls


async def test_missing_notify_notify_falls_back_to_the_phone(
    hass: HomeAssistant, setup_entry: SetupEntry, spoken: list[dict]
) -> None:
    """Without notify.notify the push goes to the only phone."""
    phone = _phone(hass)
    entry = await setup_entry({"notify_target": "notify.notify"})
    manager = hass.data[DOMAIN][entry.entry_id]
    await manager.async_send_to_mobile("Frage", "Antwort", ECHO)
    await hass.async_block_till_done()
    assert phone == [{"title": "Schlaue Antworten: Frage", "message": "Antwort"}]


async def test_no_target_sends_nothing_and_confirms_nothing(
    hass: HomeAssistant, setup_entry: SetupEntry, spoken: list[dict]
) -> None:
    """With no phone at all nothing fails and Alexa does not claim it was sent."""
    entry = await setup_entry(
        {"notify_target": "notify.notify", "mobile_confirmation": "Ist auf dem Handy."}
    )
    manager = hass.data[DOMAIN][entry.entry_id]
    await manager.async_send_to_mobile("Frage", "Antwort", ECHO)
    await hass.async_block_till_done()
    assert not [call for call in spoken if call.get("message") == "Ist auf dem Handy."]


async def test_a_configured_target_wins(
    hass: HomeAssistant, setup_entry: SetupEntry, spoken: list[dict]
) -> None:
    """An existing target is used even when there are other phones."""
    first = _phone(hass, "mobile_app_iphone")
    second = _phone(hass, "mobile_app_ipad")
    entry = await setup_entry({"notify_target": "notify.mobile_app_ipad"})
    manager = hass.data[DOMAIN][entry.entry_id]
    await manager.async_send_to_mobile("Frage", "Antwort", ECHO, confirm=False)
    await hass.async_block_till_done()
    assert not first
    assert len(second) == 1


async def test_new_setup_starts_with_the_phone(hass: HomeAssistant) -> None:
    """A new setup takes the only phone instead of notify.notify."""
    _phone(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["options"]["notify_target"] == "notify.mobile_app_iphone"


async def _settings(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    result = await hass.config_entries.options.async_init(entry_id)
    return await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "settings"}
    )


def _default(result: dict[str, Any], name: str) -> Any:
    for key in result["data_schema"].schema:
        if str(key) == name:
            return key.default()
    raise AssertionError(name)


async def test_settings_offer_the_phone(
    hass: HomeAssistant, setup_entry: SetupEntry
) -> None:
    """The form shows the phone instead of a target that does not exist."""
    _phone(hass)
    entry = await setup_entry({"notify_target": "notify.notify"})
    result = await _settings(hass, entry.entry_id)
    assert _default(result, "notify_target") == "notify.mobile_app_iphone"


async def test_settings_refuse_an_unknown_target(
    hass: HomeAssistant, setup_entry: SetupEntry
) -> None:
    """A mistyped target is pointed out before it is saved."""
    _phone(hass)
    entry = await setup_entry({"notify_target": "notify.mobile_app_iphone"})
    result = await _settings(hass, entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"notify_target": "notify.mobile_app_iphnoe"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"notify_target": "notify_target_missing"}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"notify_target": "notify.mobile_app_iphone"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["notify_target"] == "notify.mobile_app_iphone"
