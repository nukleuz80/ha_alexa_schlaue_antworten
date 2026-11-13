"""Find the Echo that a spoken room name means.

"Du stehst in der Küche" names a room, not an entity. The Echo whose name or
area fits the spoken words best, with the fewest other words, is the best match.
"""
from __future__ import annotations

import re

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

ECHO_PLATFORM = "alexa_media"
# Words that do not tell rooms apart
FILLER_WORDS = frozenset(
    {
        "echo",
        "dot",
        "show",
        "studio",
        "pop",
        "plus",
        "spot",
        "der",
        "die",
        "das",
        "dem",
        "den",
        "im",
        "in",
        "am",
        "an",
        "auf",
        "beim",
        "bei",
        "hier",
    }
)
RE_WORD = re.compile(r"[a-zäöüß0-9]+")
MIN_PART_LENGTH = 4
MIN_PART_FIT = 0.6


def room_words(text: str) -> set[str]:
    """Return the words of a name that can tell rooms apart."""
    return {
        word for word in RE_WORD.findall(text.lower()) if word not in FILLER_WORDS
    }


def echo_candidates(hass: HomeAssistant) -> dict[str, tuple[str, str]]:
    """Return Echo entity -> (name, area name)."""
    entities = er.async_get(hass)
    devices = dr.async_get(hass)
    areas = ar.async_get(hass)
    candidates: dict[str, tuple[str, str]] = {}
    for entry in entities.entities.values():
        if (
            entry.platform != ECHO_PLATFORM
            or entry.domain != "media_player"
            or entry.disabled
        ):
            continue
        state = hass.states.get(entry.entity_id)
        name = (
            str(state.attributes.get("friendly_name", "")) if state else ""
        ) or entry.name or entry.original_name or entry.entity_id
        area_id = entry.area_id
        if area_id is None and entry.device_id:
            device = devices.async_get(entry.device_id)
            area_id = device.area_id if device else None
        area = areas.async_get_area(area_id) if area_id else None
        candidates[entry.entity_id] = (name, area.name if area else "")
    return candidates


def _word_fit(spoken: str, word: str) -> float:
    """Return how well a spoken word fits a word of a name, from 0 to 1.

    "jonathans" fits "jonathan" and "küche" fits "waschküche", but less well
    than the whole word.
    """
    if spoken == word:
        return 1.0
    short, long_ = sorted((spoken, word), key=len)
    if len(short) >= MIN_PART_LENGTH and short in long_:
        fit = len(short) / len(long_)
        return fit if fit >= MIN_PART_FIT else 0.0
    return 0.0


def best_echo(spoken: str, candidates: dict[str, tuple[str, str]]) -> str | None:
    """Return the Echo whose name or area fits the spoken room best, or None."""
    wanted = room_words(spoken)
    if not wanted:
        return None
    best: tuple[float, int, str] | None = None
    for entity_id, (name, area) in candidates.items():
        name_words = room_words(name)
        words = name_words | room_words(area)
        score = sum(
            max((_word_fit(part, word) for word in words), default=0.0)
            for part in wanted
        )
        if score <= 0:
            continue
        # Words of the name that were not said make a match less likely
        extra = sum(
            1
            for word in name_words
            if all(_word_fit(part, word) == 0 for part in wanted)
        )
        if best is None or (score, -extra) > best[:2]:
            best = (score, -extra, entity_id)
    return best[2] if best else None
