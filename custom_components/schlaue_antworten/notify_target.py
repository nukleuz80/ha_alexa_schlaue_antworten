"""Find the notify service that reaches the phone."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import DEFAULT_NOTIFY_TARGET

PHONE_PREFIX = "notify.mobile_app_"


def _split(target: str) -> tuple[str, str]:
    """Return domain and service of a target like notify.mobile_app_x."""
    return "notify", target.strip().removeprefix("notify.")


def notify_services(hass: HomeAssistant) -> list[str]:
    """Return every notify service, phones first."""
    names = [f"notify.{name}" for name in hass.services.async_services_for_domain("notify")]
    return sorted(names, key=lambda name: (not name.startswith(PHONE_PREFIX), name))


def phone_targets(hass: HomeAssistant) -> list[str]:
    """Return the notify services of the companion app."""
    return [name for name in notify_services(hass) if name.startswith(PHONE_PREFIX)]


def target_exists(hass: HomeAssistant, target: str) -> bool:
    """Return whether the notify service of a target is registered."""
    domain, service = _split(target)
    return bool(service) and hass.services.has_service(domain, service)


def default_notify_target(hass: HomeAssistant) -> str:
    """Return the target a new setup starts with: the only phone, if there is one."""
    phones = phone_targets(hass)
    return phones[0] if len(phones) == 1 else DEFAULT_NOTIFY_TARGET


def resolve_notify_target(hass: HomeAssistant, configured: str) -> str | None:
    """Return the target to send to, or None when nothing reaches a phone.

    A target that does not exist (such as notify.notify, which many systems
    lack) falls back to the only phone with the companion app.
    """
    target = (configured or "").strip() or DEFAULT_NOTIFY_TARGET
    if target_exists(hass, target):
        return target if target.startswith("notify.") else f"notify.{target}"
    phones = phone_targets(hass)
    if len(phones) == 1:
        return phones[0]
    return None
