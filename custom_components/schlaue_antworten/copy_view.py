"""Page with copy buttons for the skill code and the voice model.

The options form can only show plain text fields, so the skill step links to
this page. The link is signed and expires, because the skill code contains
the secret webhook address.
"""

from __future__ import annotations

from datetime import timedelta
from html import escape

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.components.http.auth import async_sign_path
from homeassistant.core import HomeAssistant
from homeassistant.helpers.network import NoURLAvailableError

from .const import DOMAIN

COPY_URL = f"/api/{DOMAIN}/skill_copy"
LINK_MINUTES = 30
DATA_VIEW = f"{DOMAIN}_copy_view"

PAGE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>Schlaue Antworten – Skill kopieren</title>
<style>
  :root {{ color-scheme: light dark; --accent: #03a9f4; }}
  body {{ font-family: system-ui, sans-serif; margin: 0 auto; max-width: 960px;
         padding: 16px; line-height: 1.4; }}
  h1 {{ font-size: 1.4em; }}
  section {{ margin: 24px 0; }}
  .head {{ display: flex; align-items: center; justify-content: space-between;
           gap: 12px; flex-wrap: wrap; }}
  h2 {{ font-size: 1.1em; margin: 0; }}
  button {{ background: var(--accent); color: #fff; border: 0; border-radius: 8px;
            font-size: 1em; min-height: 44px; padding: 0 20px; cursor: pointer; }}
  button.done {{ background: #43a047; }}
  textarea {{ width: 100%; box-sizing: border-box; height: 260px; margin-top: 8px;
              font-family: ui-monospace, monospace; font-size: 12px; }}
  .warn {{ color: #e65100; font-weight: 600; }}
  .error {{ color: #c62828; }}
</style>
</head>
<body>
<h1>📋 Schlaue Antworten – Skill kopieren</h1>
<p>Knopf drücken, dann in der Alexa-Entwicklerkonsole einfügen.</p>
{sections}
<p class="warn">Der Skill-Code enthält deine geheime Adresse. Gib ihn nicht weiter.</p>
<p><button type="button" onclick="window.close()">Fertig – Tab schließen</button></p>
<script>
async function copyText(id, button) {{
  const field = document.getElementById(id);
  try {{
    await navigator.clipboard.writeText(field.value);
  }} catch (err) {{
    // Without HTTPS the clipboard API is missing: copy the old way
    field.focus();
    field.select();
    document.execCommand("copy");
  }}
  const label = button.textContent;
  button.textContent = "✅ Kopiert";
  button.classList.add("done");
  setTimeout(() => {{ button.textContent = label; button.classList.remove("done"); }}, 2000);
}}
</script>
</body>
</html>
"""

SECTION = """<section>
<div class="head"><h2>{title}</h2>
<button type="button" onclick="copyText('{field}', this)">📋 {button}</button></div>
<p>{hint}</p>
<textarea id="{field}" readonly>{text}</textarea>
</section>"""

ERROR = '<section><h2>{title}</h2><p class="error">{text}</p></section>'


def async_register_copy_view(hass: HomeAssistant) -> None:
    """Register the page once, however often the entry is reloaded."""
    if hass.data.get(DATA_VIEW):
        return
    hass.http.register_view(SkillCopyView())
    hass.data[DATA_VIEW] = True


def async_copy_link(hass: HomeAssistant) -> str:
    """Return a signed, expiring link to the page."""
    return async_sign_path(hass, COPY_URL, timedelta(minutes=LINK_MINUTES))


class SkillCopyView(HomeAssistantView):
    """Show the skill code and the voice model with copy buttons."""

    url = COPY_URL
    name = f"api:{DOMAIN}:skill_copy"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        """Return the page."""
        hass: HomeAssistant = request.app["hass"]
        managers = list(hass.data.get(DOMAIN, {}).values())
        if not managers:
            return web.Response(status=404)
        skill = managers[0].skill
        sections = [
            SECTION.format(
                title="1. Sprachmodell",
                field="model",
                button="Sprachmodell kopieren",
                hint="Build → Interaction Model → JSON Editor: alles ersetzen, "
                "Save, dann Build.",
                text=escape(skill.get_interaction_model()),
            )
        ]
        try:
            code = skill.get_skill_code()
        except NoURLAvailableError:
            sections.append(
                ERROR.format(
                    title="2. Skill-Code",
                    text="Home Assistant hat keine öffentliche HTTPS-Adresse "
                    "(z. B. Nabu Casa). Ohne sie erreicht der Skill Home Assistant "
                    "nicht.",
                )
            )
        else:
            sections.append(
                SECTION.format(
                    title="2. Skill-Code",
                    field="code",
                    button="Skill-Code kopieren",
                    hint="Code → lambda_function.py: alles ersetzen, dann Deploy.",
                    text=escape(code),
                )
            )
        return web.Response(
            text=PAGE.format(sections="\n".join(sections)),
            content_type="text/html",
            headers={"Cache-Control": "no-store"},
        )
