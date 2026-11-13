"""Hands Print's actions to voice assistants as Assist LLM tools.

Home Assistant (2026.11) asks every integration's llm.py for tools; without
this file an assistant sees none of these actions.
"""

from __future__ import annotations

from homeassistant.components.llm import LLMTools
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.llm import LLM_API_ASSIST, ActionTool, LLMContext

from .const import DOMAIN

# Printing the shopping list is the user's exposed script, so only recipes are here.
ACTIONS = ("recipe",)

# Some agents load tools on demand (tool search): this line is how they
# learn the tools exist.
PROMPT = (
    "ha_print__recipe prints a saved recipe on the receipt printer; get the"
    " recipe's ID from ha_recipes__search first."
)


@callback
def async_get_tools(
    hass: HomeAssistant, llm_context: LLMContext, api_id: str
) -> LLMTools | None:
    """Return Print's tools for the Assist API."""
    if api_id != LLM_API_ASSIST:
        return None
    tools = [
        ActionTool(hass, DOMAIN, action)
        for action in ACTIONS
        if hass.services.has_service(DOMAIN, action)
    ]
    return LLMTools(tools=tools, prompt=PROMPT) if tools else None
