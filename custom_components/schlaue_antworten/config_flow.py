"""Config flow and options flow for Schlaue Antworten."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_ABORT_PROMPT,
    CONF_ANNOUNCE_MODEL,
    CONF_DEFAULT_ECHO,
    CONF_DIALOG_PROMPT,
    CONF_ENABLE_DETAILED_FOLLOWUP,
    CONF_ENABLE_HA_CONTEXT,
    CONF_ENABLE_LOGGING,
    CONF_FALLBACK_AGENT,
    CONF_FOLLOWUP_PROMPT,
    CONF_GOODBYE_TEXT,
    CONF_PRIMARY_AGENT,
    CONF_PROMPT_DETAILED,
    CONF_PROMPT_SHORT,
    CONF_RETRY_PROMPT,
    CONF_SHORT_ANSWERS,
    DEFAULT_ABORT_PROMPT,
    DEFAULT_ANNOUNCE_MODEL,
    DEFAULT_DIALOG_PROMPT,
    DEFAULT_ECHO,
    DEFAULT_ENABLE_DETAILED_FOLLOWUP,
    DEFAULT_ENABLE_HA_CONTEXT,
    DEFAULT_ENABLE_LOGGING,
    DEFAULT_FALLBACK_AGENT,
    DEFAULT_FOLLOWUP_PROMPT,
    DEFAULT_GOODBYE_TEXT,
    DEFAULT_PRIMARY_AGENT,
    DEFAULT_PROMPT_DETAILED,
    DEFAULT_PROMPT_SHORT,
    DEFAULT_RETRY_PROMPT,
    DEFAULT_SHORT_ANSWERS,
    DOMAIN,
)


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
                    CONF_DEFAULT_ECHO: DEFAULT_ECHO,
                    CONF_DIALOG_PROMPT: DEFAULT_DIALOG_PROMPT,
                    CONF_ANNOUNCE_MODEL: DEFAULT_ANNOUNCE_MODEL,
                    CONF_SHORT_ANSWERS: DEFAULT_SHORT_ANSWERS,
                    CONF_ENABLE_LOGGING: DEFAULT_ENABLE_LOGGING,
                    CONF_ENABLE_HA_CONTEXT: DEFAULT_ENABLE_HA_CONTEXT,
                    CONF_ENABLE_DETAILED_FOLLOWUP: DEFAULT_ENABLE_DETAILED_FOLLOWUP,
                    CONF_FOLLOWUP_PROMPT: DEFAULT_FOLLOWUP_PROMPT,
                    CONF_GOODBYE_TEXT: DEFAULT_GOODBYE_TEXT,
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
            menu_options=["settings", "history"],
        )

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage configuration and prompts."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self.config_entry.options

        data_schema = vol.Schema(
            {
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
                    CONF_ENABLE_LOGGING,
                    default=opts.get(CONF_ENABLE_LOGGING, DEFAULT_ENABLE_LOGGING),
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_ENABLE_HA_CONTEXT,
                    default=opts.get(CONF_ENABLE_HA_CONTEXT, DEFAULT_ENABLE_HA_CONTEXT),
                ): selector.BooleanSelector(),
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
