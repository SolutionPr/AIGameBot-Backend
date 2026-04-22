from typing import Any


def validate_generated_game_config(config: dict[str, Any]) -> dict[str, Any]:
    required_keys = {"template", "title", "difficulty", "theme", "rules", "assets"}
    missing = required_keys - set(config.keys())
    if missing:
        raise ValueError(f"Generated config missing required keys: {missing}")

    required_difficulty_keys = {"level", "enemySpeed", "playerLives", "spawnRate"}
    missing_difficulty = required_difficulty_keys - set(config.get("difficulty", {}).keys())
    if missing_difficulty:
        raise ValueError(f"difficulty block missing keys: {missing_difficulty}")

    required_theme_keys = {"style", "primaryColor", "accentColor", "environment"}
    missing_theme = required_theme_keys - set(config.get("theme", {}).keys())
    if missing_theme:
        raise ValueError(f"theme block missing keys: {missing_theme}")

    if not isinstance(config.get("title"), str) or not config["title"].strip():
        raise ValueError("'title' must be a non-empty string.")

    if not isinstance(config.get("template"), str) or not config["template"].strip():
        raise ValueError("'template' must be a non-empty string.")

    config["template"] = config["template"].strip().lower()
    if isinstance(config.get("difficulty"), dict):
        level = config["difficulty"].get("level", "")
        config["difficulty"]["level"] = str(level).strip().lower()

    return config
