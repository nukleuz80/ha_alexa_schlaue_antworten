"""Tests for finding the Echo a spoken room name means."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.schlaue_antworten.echo_match import (
    best_echo,
    echo_candidates,
    room_words,
)

ECHOS = {
    "media_player.echo_show_kuche": ("Echo Show - Küche", "Küche"),
    "media_player.echo_dot_bad": ("Echo Dot - Bad", "Alexa"),
    "media_player.echo_bad_waschkuche": ("Echo - Bad Waschküche", ""),
    "media_player.wohnzimmer_echo_dot": ("Wohnzimmer Echo Dot", ""),
    "media_player.mama_echo_dot_wohnzimmer": ("Mama Echo Dot Wohnzimmer", "Alexa"),
    "media_player.jonathan_echo_dot": ("Jonathan Echo Dot", "Alexa"),
    "media_player.jans_echo_dot_garten": ("Jans Echo Dot - Garten", "Alexa"),
}


def test_room_words() -> None:
    """Articles and model names do not tell rooms apart."""
    assert room_words("Echo Show - Küche") == {"küche"}
    assert room_words("in der Küche") == {"küche"}


def test_best_echo() -> None:
    """The Echo with all spoken words and the fewest others wins."""
    assert best_echo("der küche", ECHOS) == "media_player.echo_show_kuche"
    assert best_echo("dem bad", ECHOS) == "media_player.echo_dot_bad"
    assert best_echo("wohnzimmer", ECHOS) == "media_player.wohnzimmer_echo_dot"
    assert best_echo("mamas wohnzimmer", ECHOS) == (
        "media_player.mama_echo_dot_wohnzimmer"
    )
    assert best_echo("jonathans zimmer", ECHOS) == "media_player.jonathan_echo_dot"
    assert best_echo("garten", ECHOS) == "media_player.jans_echo_dot_garten"
    assert best_echo("waschküche", ECHOS) == "media_player.echo_bad_waschkuche"
    assert best_echo("keller", ECHOS) is None
    assert best_echo("der", ECHOS) is None


async def test_echo_candidates(hass: HomeAssistant) -> None:
    """Only Echos from Alexa Media are candidates, with their name."""
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "media_player", "alexa_media", "serial1", suggested_object_id="echo_show_kuche"
    )
    registry.async_get_or_create(
        "media_player", "cast", "tv1", suggested_object_id="fernseher"
    )
    hass.states.async_set(
        "media_player.echo_show_kuche", "idle", {"friendly_name": "Echo Show - Küche"}
    )
    assert echo_candidates(hass) == {
        "media_player.echo_show_kuche": ("Echo Show - Küche", "")
    }
