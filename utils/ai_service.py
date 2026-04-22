import json

import requests
from django.conf import settings

from .validators import validate_generated_game_config


SYSTEM_PROMPT = """You are a creative game configuration generator. Convert any user prompt into a fully structured game config JSON.

RULES:
- title: Invent a unique, creative game title based on the prompt. Never use generic names.
- template: Invent a game type that best fits the prompt (e.g. runner, shooter, puzzle, platformer, rpg, stealth, racing, survival, tower-defense, fighting, strategy - or invent a new one if needed).
- difficulty.level: Invent a fitting difficulty label from the prompt context (e.g. easy, medium, hard, extreme, nightmare, casual, insane - or invent one that fits the game's tone).
- difficulty.enemySpeed: integer 1-10 scaled to difficulty
- difficulty.playerLives: integer 1-10 scaled to difficulty
- difficulty.spawnRate: integer 1-10 scaled to difficulty
- difficulty.extraMechanics: list of any additional difficulty-specific mechanics (can be empty)
- theme.style: Invent a theme name that fits the prompt context (e.g. cyberpunk, medieval, underwater, apocalyptic, dreamscape - or invent one).
- theme.primaryColor / accentColor: Hex colors that match the theme mood
- theme.environment: A vivid one-line description of the game world
- theme.atmosphere: Overall mood/feel of the game world
- rules.objective: Clear win condition
- rules.timeLimit: null or number of seconds
- rules.scoring: How player earns points
- rules.specialMechanics: List of unique gameplay mechanics derived from the prompt (be creative, at least 2)
- rules.playerAbilities: List of what the player can do
- assets.playerSprite: Visual description of the player character
- assets.background: Visual description of backgrounds
- assets.enemies: List of enemy types with brief descriptions
- assets.powerUps: List of power-up items (at least 2)
- assets.soundtrack: Music style/mood description

Always respond with ONLY valid JSON (no markdown, no explanation) in this exact structure:
{
  "title": "...",
  "template": "...",
  "difficulty": {
    "level": "...",
    "enemySpeed": 1-10,
    "playerLives": 1-10,
    "spawnRate": 1-10,
    "extraMechanics": ["..."]
  },
  "theme": {
    "style": "...",
    "primaryColor": "#...",
    "accentColor": "#...",
    "environment": "...",
    "atmosphere": "..."
  },
  "rules": {
    "objective": "...",
    "timeLimit": null,
    "scoring": "...",
    "specialMechanics": ["...", "..."],
    "playerAbilities": ["...", "..."]
  },
  "assets": {
    "playerSprite": "...",
    "background": "...",
    "enemies": ["...", "..."],
    "powerUps": ["...", "..."],
    "soundtrack": "..."
  }
}"""


class GameConfigGenerationError(Exception):
    """Raised when AI generation or JSON parsing fails."""


def _clean_json_text(raw_text: str) -> str:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    return cleaned


def _extract_message_text(message) -> str:
    return "".join(
        block.text for block in message.content
        if hasattr(block, "text")
    )


def generate_game_config(prompt: str) -> dict:
    """
    Sends a prompt to Anthropic and returns a validated game config.
    """
    try:
        import anthropic
    except ModuleNotFoundError as exc:
        raise GameConfigGenerationError(
            "The anthropic package is not installed. Install project dependencies to enable game generation."
        ) from exc

    api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
    if not api_key:
        raise GameConfigGenerationError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file before calling /api/generate/."
        )

    client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIConnectionError as exc:
        raise GameConfigGenerationError(f"Connection to Anthropic API failed: {str(exc)}") from exc
    except anthropic.AuthenticationError as exc:
        raise GameConfigGenerationError("Invalid Anthropic API key. Check your ANTHROPIC_API_KEY setting.") from exc
    except anthropic.RateLimitError as exc:
        raise GameConfigGenerationError("Anthropic API rate limit exceeded. Please try again later.") from exc
    except anthropic.APIError as exc:
        raise GameConfigGenerationError(f"Anthropic API error: {str(exc)}") from exc

    raw_text = _extract_message_text(message)
    cleaned = _clean_json_text(raw_text)

    try:
        config = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise GameConfigGenerationError(
            f"Failed to parse AI response as JSON: {str(exc)}. Raw response: {raw_text[:200]}"
        ) from exc

    try:
        return validate_generated_game_config(config)
    except ValueError as exc:
        raise GameConfigGenerationError(str(exc)) from exc


def generate_game_config_with_groq(prompt: str) -> dict:
    """
    Generate a structured game config using Groq's OpenAI-compatible API.
    """
    api_key = getattr(settings, "GROQ_API_KEY", "")
    if not api_key:
        raise GameConfigGenerationError(
            "GROQ_API_KEY is not set. Add it to your .env file before calling /api/generate/."
        )

    model = getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )
        response.raise_for_status()
        response_data = response.json()
    except requests.RequestException as exc:
        raise GameConfigGenerationError(f"Connection to Groq API failed: {str(exc)}") from exc
    except ValueError as exc:
        raise GameConfigGenerationError(f"Groq API returned invalid JSON: {str(exc)}") from exc

    try:
        raw_text = response_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GameConfigGenerationError("Groq API response did not contain a generated message.") from exc

    cleaned = _clean_json_text(raw_text)

    try:
        config = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise GameConfigGenerationError(
            f"Failed to parse AI response as JSON: {str(exc)}. Raw response: {raw_text[:200]}"
        ) from exc

    try:
        return validate_generated_game_config(config)
    except ValueError as exc:
        raise GameConfigGenerationError(str(exc)) from exc
