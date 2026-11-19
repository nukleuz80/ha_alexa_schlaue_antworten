"""Config flow and options flow for Schlaue Antworten."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.network import NoURLAvailableError

from .const import (
    CONF_ABORT_PROMPT,
    CONF_ANNOUNCE_MODEL,
    CONF_CLAUDE_ALLOW_APP,
    CONF_CLAUDE_ECHOS,
    CONF_CLAUDE_TOKEN,
    CONF_CLAUDE_URL,
    CONF_ANSWER_BUDGET,
    CONF_CUSTOM_KNOWLEDGE,
    CONF_DEFAULT_ECHO,
    CONF_DIALOG_PROMPT,
    CONF_DIRECT_QUERY_PREFIXES,
    CONF_ENABLE_DETAILED_FOLLOWUP,
    CONF_ENABLE_DIRECT_QUERY,
    CONF_ENABLE_HA_CONTEXT,
    CONF_ENABLE_LOGGING,
    CONF_FALLBACK_AGENT,
    CONF_FOLLOWUP_PROMPT,
    CONF_GOODBYE_TEXT,
    CONF_INTERACTIVE_CONFIRM_PROMPT,
    CONF_INVOCATION_NAME,
    CONF_LATE_TEXT,
    CONF_MOBILE_CONFIRMATION,
    CONF_NOTIFY_TARGET,
    CONF_PRIMARY_AGENT,
    CONF_PRIMARY_TIMEOUT,
    CONF_PROMPT_DETAILED,
    CONF_PROMPT_SHORT,
    CONF_RETRY_PROMPT,
    CONF_SHORT_ANSWERS,
    CONF_SKILL_KEEP_OPEN,
    CONF_VOICE_PATH,
    DEFAULT_ABORT_PROMPT,
    DEFAULT_ANNOUNCE_MODEL,
    DEFAULT_ANSWER_BUDGET,
    DEFAULT_CLAUDE_ALLOW_APP,
    DEFAULT_CUSTOM_KNOWLEDGE,
    DEFAULT_DIALOG_PROMPT,
    DEFAULT_DIRECT_QUERY_PREFIXES,
    DEFAULT_ECHO,
    DEFAULT_ENABLE_DETAILED_FOLLOWUP,
    DEFAULT_ENABLE_DIRECT_QUERY,
    DEFAULT_ENABLE_HA_CONTEXT,
    DEFAULT_ENABLE_LOGGING,
    DEFAULT_FALLBACK_AGENT,
    DEFAULT_FOLLOWUP_PROMPT,
    DEFAULT_GOODBYE_TEXT,
    DEFAULT_INTERACTIVE_CONFIRM_PROMPT,
    DEFAULT_INVOCATION_NAME,
    DEFAULT_LATE_TEXT,
    DEFAULT_MOBILE_CONFIRMATION,
    DEFAULT_NOTIFY_TARGET,
    DEFAULT_PRIMARY_AGENT,
    DEFAULT_PRIMARY_TIMEOUT,
    DEFAULT_PROMPT_DETAILED,
    DEFAULT_PROMPT_SHORT,
    DEFAULT_RETRY_PROMPT,
    DEFAULT_SHORT_ANSWERS,
    DEFAULT_SKILL_KEEP_OPEN,
    DEFAULT_VOICE_PATH,
    DOMAIN,
    VOICE_PATHS,
)
from .skill_model import is_valid_invocation


class SchlaueAntwortenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Schlaue Antworten."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial setup step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title="Schlaue Antworten",
                data={},
                options={
                    CONF_PRIMARY_AGENT: DEFAULT_PRIMARY_AGENT,
                    CONF_FALLBACK_AGENT: DEFAULT_FALLBACK_AGENT,
                    CONF_PRIMARY_TIMEOUT: DEFAULT_PRIMARY_TIMEOUT,
                    CONF_ANSWER_BUDGET: DEFAULT_ANSWER_BUDGET,
                    CONF_LATE_TEXT: DEFAULT_LATE_TEXT,
                    CONF_VOICE_PATH: DEFAULT_VOICE_PATH,
                    CONF_DEFAULT_ECHO: DEFAULT_ECHO,
                    CONF_DIALOG_PROMPT: DEFAULT_DIALOG_PROMPT,
                    CONF_ANNOUNCE_MODEL: DEFAULT_ANNOUNCE_MODEL,
                    CONF_SHORT_ANSWERS: DEFAULT_SHORT_ANSWERS,
                    CONF_ENABLE_LOGGING: DEFAULT_ENABLE_LOGGING,
                    CONF_ENABLE_HA_CONTEXT: DEFAULT_ENABLE_HA_CONTEXT,
                    CONF_CUSTOM_KNOWLEDGE: DEFAULT_CUSTOM_KNOWLEDGE,
                    CONF_ENABLE_DETAILED_FOLLOWUP: DEFAULT_ENABLE_DETAILED_FOLLOWUP,
                    CONF_FOLLOWUP_PROMPT: DEFAULT_FOLLOWUP_PROMPT,
                    CONF_GOODBYE_TEXT: DEFAULT_GOODBYE_TEXT,
                    CONF_INTERACTIVE_CONFIRM_PROMPT: DEFAULT_INTERACTIVE_CONFIRM_PROMPT,
                    CONF_NOTIFY_TARGET: DEFAULT_NOTIFY_TARGET,
                    CONF_MOBILE_CONFIRMATION: DEFAULT_MOBILE_CONFIRMATION,
                    CONF_RETRY_PROMPT: DEFAULT_RETRY_PROMPT,
                    CONF_ABORT_PROMPT: DEFAULT_ABORT_PROMPT,
                    CONF_PROMPT_SHORT: DEFAULT_PROMPT_SHORT,
                    CONF_PROMPT_DETAILED: DEFAULT_PROMPT_DETAILED,
                },
            )

        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return SchlaueAntwortenOptionsFlow()


class SchlaueAntwortenOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Schlaue Antworten."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show main options menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["settings", "skill", "echos", "claude", "history"],
        )

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage configuration and prompts."""
        if user_input is not None:
            # Options of the other steps (skill, Echos, Claude) live in the same
            # entry and must survive
            return self.async_create_entry(
                title="", data={**self.config_entry.options, **user_input}
            )

        opts = self.config_entry.options

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_VOICE_PATH,
                    default=opts.get(CONF_VOICE_PATH, DEFAULT_VOICE_PATH),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=VOICE_PATHS,
                        translation_key=CONF_VOICE_PATH,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_PRIMARY_AGENT,
                    default=opts.get(CONF_PRIMARY_AGENT, DEFAULT_PRIMARY_AGENT),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="conversation")
                ),
                vol.Optional(
                    CONF_FALLBACK_AGENT,
                    default=opts.get(CONF_FALLBACK_AGENT, DEFAULT_FALLBACK_AGENT),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="conversation")
                ),
                vol.Required(
                    CONF_PRIMARY_TIMEOUT,
                    default=opts.get(CONF_PRIMARY_TIMEOUT, DEFAULT_PRIMARY_TIMEOUT),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=15,
                        step=0.5,
                        unit_of_measurement="s",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_ANSWER_BUDGET,
                    default=opts.get(CONF_ANSWER_BUDGET, DEFAULT_ANSWER_BUDGET),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=30,
                        step=0.5,
                        unit_of_measurement="s",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_DEFAULT_ECHO,
                    default=opts.get(CONF_DEFAULT_ECHO, DEFAULT_ECHO),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="media_player")
                ),
                vol.Required(
                    CONF_DIALOG_PROMPT,
                    default=opts.get(CONF_DIALOG_PROMPT, DEFAULT_DIALOG_PROMPT),
                ): selector.TextSelector(),
                vol.Required(
                    CONF_ANNOUNCE_MODEL,
                    default=opts.get(CONF_ANNOUNCE_MODEL, DEFAULT_ANNOUNCE_MODEL),
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_SHORT_ANSWERS,
                    default=opts.get(CONF_SHORT_ANSWERS, DEFAULT_SHORT_ANSWERS),
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_ENABLE_DIRECT_QUERY,
                    default=opts.get(
                        CONF_ENABLE_DIRECT_QUERY,
                        DEFAULT_ENABLE_DIRECT_QUERY,
                    ),
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_DIRECT_QUERY_PREFIXES,
                    default=opts.get(
                        CONF_DIRECT_QUERY_PREFIXES,
                        DEFAULT_DIRECT_QUERY_PREFIXES,
                    ),
                ): selector.TextSelector(),
                vol.Required(
                    CONF_ENABLE_LOGGING,
                    default=opts.get(CONF_ENABLE_LOGGING, DEFAULT_ENABLE_LOGGING),
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_ENABLE_HA_CONTEXT,
                    default=opts.get(CONF_ENABLE_HA_CONTEXT, DEFAULT_ENABLE_HA_CONTEXT),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_CUSTOM_KNOWLEDGE,
                    default=opts.get(CONF_CUSTOM_KNOWLEDGE, DEFAULT_CUSTOM_KNOWLEDGE),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Required(
                    CONF_ENABLE_DETAILED_FOLLOWUP,
                    default=opts.get(
                        CONF_ENABLE_DETAILED_FOLLOWUP,
                        DEFAULT_ENABLE_DETAILED_FOLLOWUP,
                    ),
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_FOLLOWUP_PROMPT,
                    default=opts.get(
                        CONF_FOLLOWUP_PROMPT,
                        DEFAULT_FOLLOWUP_PROMPT,
                    ),
                ): selector.TextSelector(),
                vol.Required(
                    CONF_GOODBYE_TEXT,
                    default=opts.get(
                        CONF_GOODBYE_TEXT,
                        DEFAULT_GOODBYE_TEXT,
                    ),
                ): selector.TextSelector(),
                vol.Required(
                    CONF_INTERACTIVE_CONFIRM_PROMPT,
                    default=opts.get(
                        CONF_INTERACTIVE_CONFIRM_PROMPT,
                        DEFAULT_INTERACTIVE_CONFIRM_PROMPT,
                    ),
                ): selector.TextSelector(),
                vol.Required(
                    CONF_NOTIFY_TARGET,
                    default=opts.get(
                        CONF_NOTIFY_TARGET,
                        DEFAULT_NOTIFY_TARGET,
                    ),
                ): selector.TextSelector(),
                vol.Required(
                    CONF_MOBILE_CONFIRMATION,
                    default=opts.get(
                        CONF_MOBILE_CONFIRMATION,
                        DEFAULT_MOBILE_CONFIRMATION,
                    ),
                ): selector.TextSelector(),
                vol.Required(
                    CONF_LATE_TEXT,
                    default=opts.get(CONF_LATE_TEXT, DEFAULT_LATE_TEXT),
                ): selector.TextSelector(),
                vol.Required(
                    CONF_RETRY_PROMPT,
                    default=opts.get(
                        CONF_RETRY_PROMPT,
                        DEFAULT_RETRY_PROMPT,
                    ),
                ): selector.TextSelector(),
                vol.Required(
                    CONF_ABORT_PROMPT,
                    default=opts.get(
                        CONF_ABORT_PROMPT,
                        DEFAULT_ABORT_PROMPT,
                    ),
                ): selector.TextSelector(),
                vol.Required(
                    CONF_PROMPT_SHORT,
                    default=opts.get(
                        CONF_PROMPT_SHORT,
                        DEFAULT_PROMPT_SHORT,
                    ),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Required(
                    CONF_PROMPT_DETAILED,
                    default=opts.get(
                        CONF_PROMPT_DETAILED,
                        DEFAULT_PROMPT_DETAILED,
                    ),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
            }
        )

        return self.async_show_form(
            step_id="settings",
            data_schema=data_schema,
        )

    async def async_step_skill(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the code and voice model for the own Alexa skill."""
        manager = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id)
        if manager is None:
            return self.async_abort(reason="not_loaded")
        skill = manager.skill
        options = dict(self.config_entry.options)
        errors: dict[str, str] = {}

        if user_input is not None:
            invocation = " ".join(
                str(user_input.get(CONF_INVOCATION_NAME, "")).lower().split()
            )
            if not is_valid_invocation(invocation):
                errors[CONF_INVOCATION_NAME] = "invalid_invocation"
            else:
                if user_input.get("reset_skill"):
                    await skill.async_reset()
                options[CONF_INVOCATION_NAME] = invocation
                options[CONF_SKILL_KEEP_OPEN] = bool(
                    user_input.get(CONF_SKILL_KEEP_OPEN, DEFAULT_SKILL_KEEP_OPEN)
                )
                return self.async_create_entry(title="", data=options)

        copy_field = selector.TextSelector(selector.TextSelectorConfig(multiline=True))
        schema: dict[Any, Any] = {
            vol.Required(
                CONF_INVOCATION_NAME,
                default=options.get(CONF_INVOCATION_NAME, DEFAULT_INVOCATION_NAME),
            ): selector.TextSelector(),
            vol.Optional(
                CONF_SKILL_KEEP_OPEN,
                default=options.get(CONF_SKILL_KEEP_OPEN, DEFAULT_SKILL_KEEP_OPEN),
            ): selector.BooleanSelector(),
        }
        try:
            skill_code = skill.get_skill_code()
        except NoURLAvailableError:
            errors["base"] = "no_public_url"
        else:
            schema[
                vol.Optional("skill_code", description={"suggested_value": skill_code})
            ] = copy_field
        schema[
            vol.Optional(
                "interaction_model",
                description={"suggested_value": skill.get_interaction_model()},
            )
        ] = copy_field
        schema[vol.Optional("reset_skill", default=False)] = selector.BooleanSelector()

        last = skill.last_request
        return self.async_show_form(
            step_id="skill",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={
                "active": "✅" if skill.is_active else "❌",
                "linked": "✅" if skill.is_linked else "❌",
                "last_request": (
                    f"{last['time']}: {last['text']}".replace("{", "[").replace(
                        "}", "]"
                    )
                    if last
                    else "–"
                ),
            },
        )

    async def async_step_echos(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Assign the Echos that used the own skill, or correct the assignment."""
        manager = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id)
        if manager is None:
            return self.async_abort(reason="not_loaded")
        skill = manager.skill
        # The Alexa device ids are long and secret-looking; show their end only
        labels = {
            f"…{device_id[-6:]} · {seen}": device_id
            for device_id, seen in skill.seen_devices.items()
        }
        if user_input is not None:
            await skill.async_set_device_map(
                {
                    labels[label]: str(entity_id)
                    for label, entity_id in user_input.items()
                    if label in labels and entity_id
                }
            )
            return self.async_create_entry(
                title="", data=dict(self.config_entry.options)
            )

        device_map = skill.device_map
        schema: dict[Any, Any] = {}
        for label, device_id in labels.items():
            current = device_map.get(device_id)
            schema[
                vol.Optional(
                    label,
                    description={"suggested_value": current} if current else None,
                )
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="media_player")
            )
        return self.async_show_form(
            step_id="echos",
            data_schema=vol.Schema(schema),
            description_placeholders={"count": str(len(labels))},
        )

    async def async_step_claude(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Set up the bridge that hands voice prompts to a Claude session."""
        manager = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id)
        if manager is None:
            return self.async_abort(reason="not_loaded")
        options = dict(self.config_entry.options)
        errors: dict[str, str] = {}

        if user_input is not None:
            url = str(user_input.get(CONF_CLAUDE_URL) or "").strip().rstrip("/")
            token = str(user_input.get(CONF_CLAUDE_TOKEN) or "").strip()
            if url and not url.startswith(("http://", "https://")):
                errors[CONF_CLAUDE_URL] = "invalid_url"
            elif url and not token:
                errors[CONF_CLAUDE_TOKEN] = "token_required"
            else:
                options[CONF_CLAUDE_URL] = url
                options[CONF_CLAUDE_TOKEN] = token
                options[CONF_CLAUDE_ECHOS] = [
                    str(echo) for echo in user_input.get(CONF_CLAUDE_ECHOS) or []
                ]
                options[CONF_CLAUDE_ALLOW_APP] = bool(
                    user_input.get(CONF_CLAUDE_ALLOW_APP, DEFAULT_CLAUDE_ALLOW_APP)
                )
                return self.async_create_entry(title="", data=options)

        bridge = manager.claude
        try:
            bridge.reply_url()
        except NoURLAvailableError:
            errors["base"] = "no_local_url"
        last = bridge.last_prompt
        return self.async_show_form(
            step_id="claude",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_CLAUDE_URL,
                        description={
                            "suggested_value": options.get(CONF_CLAUDE_URL, "")
                        },
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.URL)
                    ),
                    vol.Optional(
                        CONF_CLAUDE_TOKEN,
                        description={
                            "suggested_value": options.get(CONF_CLAUDE_TOKEN, "")
                        },
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        )
                    ),
                    vol.Optional(
                        CONF_CLAUDE_ECHOS,
                        default=options.get(CONF_CLAUDE_ECHOS, []),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="media_player", multiple=True
                        )
                    ),
                    vol.Optional(
                        CONF_CLAUDE_ALLOW_APP,
                        default=options.get(
                            CONF_CLAUDE_ALLOW_APP, DEFAULT_CLAUDE_ALLOW_APP
                        ),
                    ): selector.BooleanSelector(),
                }
            ),
            errors=errors,
            description_placeholders={
                "enabled": "✅" if bridge.enabled else "❌",
                "phones": str(len(manager.skill.phone_devices)),
                "last_prompt": (
                    f"{last['echo']}: {last['text']}".replace("{", "[").replace(
                        "}", "]"
                    )
                    if last
                    else "–"
                ),
            },
        )

    async def async_step_history(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Display dialog log in a dedicated dialog step."""
        if user_input is not None:
            return await self.async_step_init()

        entry_id = self.config_entry.entry_id
        manager = self.hass.data.get(DOMAIN, {}).get(entry_id)
        history_md = (
            manager.get_history_markdown()
            if manager
            else "_Noch keine Dialoge aufgezeichnet._"
        )
        # Sanitize any curly braces in user queries/output to avoid FormatJS parsing
        clean_history = history_md.replace("{", "[").replace("}", "]")

        return self.async_show_form(
            step_id="history",
            data_schema=vol.Schema({}),
            description_placeholders={"log_content": clean_history},
        )
