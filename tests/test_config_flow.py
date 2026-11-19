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
    """The options start with the menu of settings, own skill and history."""
    entry = await setup_entry()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert set(result["menu_options"]) == {"settings", "skill", "echos", "claude", "history"}


async def test_skill_step_shows_code_and_model(
    hass: HomeAssistant, setup_entry: SetupEntry
) -> None:
    """The skill step shows the code with the secret address and saves the name."""
    from homeassistant.core_config import async_process_ha_core_config

    await async_process_ha_core_config(
        hass, {"external_url": "https://example.ui.nabu.casa"}
    )
    entry = await setup_entry()
    manager = hass.data[DOMAIN][entry.entry_id]
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "skill"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    fields = {str(key): key for key in result["data_schema"].schema}
    code = fields["skill_code"].description["suggested_value"]
    secret = manager.skill.webhook_id
    assert f"https://example.ui.nabu.casa/api/webhook/{secret}" in code
    model = fields["interaction_model"].description["suggested_value"]
    assert '"invocationName": "schlaufuchs"' in model

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"invocation_name": "Schlau  Fuchs!"}
    )
    assert result["errors"] == {"invocation_name": "invalid_invocation"}

    old_secret = manager.skill.webhook_id
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "invocation_name": "Schlauer  Fuchs",
            "reset_skill": True,
            "skill_keep_open": True,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["invocation_name"] == "schlauer fuchs"
    assert entry.options["skill_keep_open"] is True
    assert entry.options["default_echo"]
    assert hass.data[DOMAIN][entry.entry_id].skill.webhook_id != old_secret


async def test_skill_step_without_public_url(
    hass: HomeAssistant, setup_entry: SetupEntry
) -> None:
    """Without a public HTTPS address the step explains why no code is shown."""
    entry = await setup_entry()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "skill"}
    )
    assert result["errors"] == {"base": "no_public_url"}
    assert "skill_code" not in {str(key) for key in result["data_schema"].schema}


async def test_settings_keep_the_invocation_name(
    hass: HomeAssistant, setup_entry: SetupEntry
) -> None:
    """Saving the settings drops neither the skill nor the Claude options."""
    entry = await setup_entry(
        {
            "invocation_name": "schlauer fuchs",
            "claude_url": "http://192.168.1.50:8765",
            "claude_echos": ["media_player.kueche"],
        }
    )
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "settings"}
    )
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["invocation_name"] == "schlauer fuchs"
    assert result["data"]["claude_url"] == "http://192.168.1.50:8765"
    assert result["data"]["claude_echos"] == ["media_player.kueche"]


async def test_echo_assignment_step(
    hass: HomeAssistant, setup_entry: SetupEntry
) -> None:
    """Echos that used the skill can be assigned and corrected in the options."""
    entry = await setup_entry()
    skill = hass.data[DOMAIN][entry.entry_id].skill
    skill._note_device("amzn1.ask.device.AAAAAA111111")
    skill._note_device("amzn1.ask.device.BBBBBB222222")
    await skill.async_set_device_map(
        {"amzn1.ask.device.AAAAAA111111": "media_player.alt"}
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "echos"}
    )
    assert result["type"] is FlowResultType.FORM
    fields = {str(key): key for key in result["data_schema"].schema}
    label_a = next(label for label in fields if label.startswith("…111111"))
    label_b = next(label for label in fields if label.startswith("…222222"))
    assert fields[label_a].description == {"suggested_value": "media_player.alt"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {label_b: "media_player.kueche"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    # The cleared field removes the old assignment
    assert skill.device_map == {
        "amzn1.ask.device.BBBBBB222222": "media_player.kueche"
    }


async def test_claude_step_saves_bridge(
    hass: HomeAssistant, setup_entry: SetupEntry
) -> None:
    """The Claude step checks and saves address, token and allowed Echos."""
    hass.config.internal_url = "http://192.168.1.10:8123"
    entry = await setup_entry()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "claude"}
    )
    assert result["step_id"] == "claude"
    assert result["errors"] == {}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"claude_url": "192.168.1.50:8765"}
    )
    assert result["errors"] == {"claude_url": "invalid_url"}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"claude_url": "http://192.168.1.50:8765"}
    )
    assert result["errors"] == {"claude_token": "token_required"}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "claude_url": "http://192.168.1.50:8765/",
            "claude_token": " geheim ",
            "claude_echos": ["media_player.test_echo"],
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options["claude_url"] == "http://192.168.1.50:8765"
    assert entry.options["claude_token"] == "geheim"
    assert entry.options["claude_echos"] == ["media_player.test_echo"]
