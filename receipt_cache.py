import gzip
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from hexbytes import HexBytes

from blockchain_fetcher import BlockchainFetcher
from web3.exceptions import TimeExhausted


RECEIPT_CACHE_DIR = Path("data/receipts")


def _fetch_receipt_with_retry(fetcher: BlockchainFetcher, tx_hash: str, max_retries: int = 5):
    delay = 1

    for attempt in range(max_retries):
        try:
            return fetcher.web3_client.eth.get_transaction_receipt(tx_hash)

        except Exception as exc:
            error_text = str(exc).lower()

            is_rate_limited = (
                "429" in error_text
                or "too many requests" in error_text
                or "rate limit" in error_text
            )

            if not is_rate_limited or attempt == max_retries - 1:
                raise

            print(f"Rate limited. Waiting {delay}s before retrying...")
            time.sleep(delay)
            delay *= 2


def _to_json_safe(value: Any) -> Any:
    if isinstance(value, HexBytes):
        return value.hex()

    if isinstance(value, dict):
        return {key: _to_json_safe(item) for key, item in value.items()}

    if isinstance(value, list):
        return [_to_json_safe(item) for item in value]

    return value


def _minimize_receipt(receipt: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "transactionHash": _to_json_safe(receipt.get("transactionHash")),
        "blockNumber": receipt.get("blockNumber"),
        "blockHash": _to_json_safe(receipt.get("blockHash")),
        "status": receipt.get("status"),
        "logs": [
            {
                "address": log.get("address"),
                "topics": _to_json_safe(log.get("topics", [])),
                "data": _to_json_safe(log.get("data")),
                "logIndex": log.get("logIndex"),
                "transactionIndex": log.get("transactionIndex"),
            }
            for log in receipt.get("logs", [])
        ],
    }


def _cache_path(block_number: int) -> Path:
    return RECEIPT_CACHE_DIR / f"block_{block_number}.json.gz"


def _load_cached_receipts(block_number: int) -> Optional[Dict[str, Any]]:
    path = _cache_path(block_number)

    if not path.exists():
        return None

    with gzip.open(path, "rt", encoding="utf-8") as file:
        return json.load(file)


def _save_cached_receipts(block_number: int, payload: Dict[str, Any]) -> None:
    RECEIPT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    path = _cache_path(block_number)

    with gzip.open(path, "wt", encoding="utf-8", compresslevel=9) as file:
        json.dump(payload, file, separators=(",", ":"))


def get_block_receipts(block_number: int) -> Dict[str, Any]:
    cached = _load_cached_receipts(block_number)

    if cached is not None:
        print(f"Loaded receipts for block {block_number} from cache")
        return cached

    print(f"Fetching receipts for block {block_number} from API")

    fetcher = BlockchainFetcher()
    block = fetcher.web3_client.eth.get_block(block_number, full_transactions=True)

    receipts = {}

    for tx in block["transactions"]:
        tx_hash = tx["hash"].hex()

        receipt = _fetch_receipt_with_retry(fetcher, tx_hash)
        time.sleep(0.15)
        minimized = _minimize_receipt(receipt)

        receipts[tx_hash] = minimized

    payload = {
        "blockNumber": block_number,
        "blockHash": block["hash"].hex(),
        "receiptCount": len(receipts),
        "receipts": receipts,
    }

    _save_cached_receipts(block_number, payload)

    return payload
