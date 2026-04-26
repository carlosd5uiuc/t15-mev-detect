import json
from pathlib import Path
from typing import Dict, Optional


TOKEN_DECIMALS_CACHE_PATH = Path("data/token_decimals.json")


def load_token_decimals_cache() -> Dict[str, int]:
    if not TOKEN_DECIMALS_CACHE_PATH.exists():
        return {}

    with open(TOKEN_DECIMALS_CACHE_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def save_token_decimals_cache(cache: Dict[str, int]) -> None:
    TOKEN_DECIMALS_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(TOKEN_DECIMALS_CACHE_PATH, "w", encoding="utf-8") as file:
        json.dump(cache, file, indent=2, sort_keys=True)


def get_cached_decimals(cache: Dict[str, int], token_address: str) -> Optional[int]:
    return cache.get(token_address.lower())


def set_cached_decimals(cache: Dict[str, int], token_address: str, decimals: int) -> None:
    cache[token_address.lower()] = decimals
