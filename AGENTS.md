# Home Assistant Development Standards & Guidelines

This project strictly adheres to the official Home Assistant developer documentation and standards as specified at [contributors.home-assistant.io](https://contributors.home-assistant.io/).

## 1. Code Style & Standards
- **Typing**: Always include `from __future__ import annotations` at the top of every Python file. Use strict, modern type hints (`dict[str, Any]`, `list[str]`, `Callable[[], None]`, `Awaitable[None]`).
- **Formatting**: Follow PEP 8 and Home Assistant conventions (conforming to `ruff` / `black`, 88 char line length, double quotes, standard import sorting: stdlib -> 3rd-party -> homeassistant -> relative local imports).
- **Asynchronous Execution**: Never run blocking operations inside the main event loop. All I/O, storage calls, and heavy computations must use `asyncio` or be offloaded via `await hass.async_add_executor_job(...)`.

## 2. Integration Architecture
- **Manifest (`manifest.json`)**:
  - Maintain complete metadata (`integration_type`, `iot_class`, `documentation`, `issue_tracker`, `codeowners`, `single_config_entry: true` if applicable).
- **Config Flow & Options Flow**:
  - Implement configuration flows inheriting from `config_entries.ConfigFlow` and `config_entries.OptionsFlowWithConfigEntry` (or `OptionsFlow`).
  - Never hardcode user-facing texts; manage all schema labels, error messages, and descriptions via `strings.json` and `translations/{lang}.json`.
  - Use `async_show_menu` for multi-step configuration tasks.
- **Entity Platform Design**:
  - Always enable `_attr_has_entity_name = True`.
  - Assign deterministic, unique identifiers via `_attr_unique_id`.
  - Provide complete device information via `device_info = DeviceInfo(...)`.
  - Leverage `_attr_translation_key` for entity naming and states.
- **Data Storage & State Management**:
  - Persist integration state through `homeassistant.helpers.storage.Store`.
  - Never modify files inside `custom_components/` at runtime. User data lives strictly in `/config/` or `.storage/`.
- **ConfigEntry Lifecycle & Reload Safety**:
  - Never invoke `async_setup_entry` manually inside an `entry.add_update_listener` callback. Always use `await hass.config_entries.async_reload(entry.entry_id)` to let Home Assistant Core manage cleanup and rebuild.
  - Every service registered in `async_setup_entry` or entity added must have a clean teardown in `async_unload_entry`.
  - Guard strictly against recursive reload loops, listener duplication, or event floods (e.g. WebSocket 4096 pending messages) that freeze the event loop or drop client connections.
- **Exception Handling & Logging**:
  - Use `_LOGGER = logging.getLogger(__name__)`.
  - Raise standard exceptions (`HomeAssistantError`, `ConfigEntryNotReady`, `ServiceValidationError`) from `homeassistant.exceptions`.
  - Do not use bare `except:` or swallow exceptions silently.

## 3. Frontend & Custom Cards
- Follow official Home Assistant Lovelace Custom Card specifications:
  - Register components with `customElements.define(...)`.
  - Implement `setConfig`, `getCardSize`, and `getStubConfig`.
  - Use official theme CSS custom properties (`var(--primary-color)`, `var(--card-background-color)`, `var(--primary-text-color)`, etc.) to support both light and dark themes seamlessly.
  - Ensure full responsiveness on mobile screens (responsive wraps, minimum touch target sizes).

## 4. Versioning, Releases & Documentation Maintenance
- **Synchronized Versioning**: Versions across all touchpoints (`manifest.json`, `brainstorm-card.js`, `brainstorm-mindmap-card.js`, `lovelace_resources`, `lovelace.yaml`, and Git tags) must strictly match and be bumped consistently on every feature or bugfix release.
- **Mandatory Git Version Tags**: Bei jedem Update, Bugfix oder Release MUSS zwingend ein passender Git-Tag (z. B. `git tag -a v1.0.1 -m "Release v1.0.1" && git push origin v1.0.1`) für das jeweilige Repository (`ha_alexa_schlaue_antworten`, `ha_brainstorm` etc.) generiert und remote gepusht werden.
- **Granular Versioning**: Develop in smaller, incremental patch steps (e.g. next is `1.0.1` bzw. `1.4.16`, etc.) unless an explicit major milestone is requested.
- **Repository README (`README.md`) & Changelog**:
  - Maintain an exhaustive, professional, and clear project description.
  - Continuously update the **Versionshistorie & Changelog** table with every release (version, date, and highlights).
  - Document all supported voice command variants (Alexa Dialog, Alexa Direct, Assist Sentences, To-do list intents).
  - Include up-to-date installation instructions for both HACS and manual methods, card configuration, and screenshots.
  - Keep version badges and cache busters strictly synchronized.

## 5. System Operations & Restart Policy
- **NO Unprompted Restarts**: NEVER restart Home Assistant (`homeassistant.restart`, `ha core restart`, supervisor restart, etc.) without explicitly asking the user for permission first. Always ask first.

## 6. Chat-Statistiken (Kontext & Token)
- Behalte am Ende jeder Antwort die einzeilige Text-Statistik für das Kontext-Gesamtkontingent bei (z. B. `📊 Kontext-Gesamtkontingent: ~XX.XXX / 1.000.000 Tokens (X,X % belegt • XXX.XXX frei)`).
- **Keine Artefakt-Karten / HTML-Boxen:** Es dürfen keine separaten Artefakte (wie `token_monitor.html` oder Artifact-Cards) dafür generiert oder eingebunden werden.


