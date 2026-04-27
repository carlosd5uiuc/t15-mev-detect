import json
from pathlib import Path
from typing import Dict


TOKEN_METADATA_CACHE_PATH = Path("data/token_metadata.json")


def load_token_metadata_cache() -> Dict[str, dict]:
    if not TOKEN_METADATA_CACHE_PATH.exists():
        return {}

    with open(TOKEN_METADATA_CACHE_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def save_token_metadata_cache(cache: Dict[str, dict]) -> None:
    TOKEN_METADATA_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(TOKEN_METADATA_CACHE_PATH, "w", encoding="utf-8") as file:
        json.dump(cache, file, indent=2, sort_keys=True)
