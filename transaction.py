import csv
from dataclasses import dataclass
from typing import Optional


@dataclass
class TransactionRow:
    # --- existing fields (DO NOT BREAK ARBITRAGE) ---
    timestamp: int
    hash: str
    chainId: str
    from_address: str
    to: str
    value: str
    nonce: str
    gas: str
    gasPrice: str
    gasTipCap: str
    gasFeeCap: str
    dataSize: int
    data4Bytes: str

    # --- NEW fields (used for front-running / sandwich / MEV) ---
    sources: Optional[str] = None
    block_height: Optional[int] = None
    block_timestamp: Optional[int] = None
    inclusion_delay_ms: Optional[int] = None
    tx_type: Optional[int] = None

    @classmethod
    def from_csv_row(cls, row: dict) -> "TransactionRow":
        return cls(
            # --- core fields ---
            timestamp=int(row["timestamp_ms"]),
            hash=row["hash"],
            chainId=row["chain_id"],
            from_address=row["from"],
            to=row["to"],
            value=row["value"],
            nonce=row["nonce"],
            gas=row["gas"],
            gasPrice=row["gas_price"],
            gasTipCap=row["gas_tip_cap"],
            gasFeeCap=row["gas_fee_cap"],
            dataSize=int(row["data_size"]),
            data4Bytes=row["data_4bytes"],

            # --- MEV / ordering context ---
            sources=row.get("sources") or None,
            block_height=int(row["included_at_block_height"]) if row.get("included_at_block_height") else None,
            block_timestamp=int(row["included_block_timestamp_ms"]) if row.get("included_block_timestamp_ms") else None,
            inclusion_delay_ms=int(row["inclusion_delay_ms"]) if row.get("inclusion_delay_ms") else None,
            tx_type=int(row["tx_type"]) if row.get("tx_type") else None,
        )


def load_transactions(file="2026-03-01-100k.csv"):
    rows = []
    with open(f"data/{file}", "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            rows.append(TransactionRow.from_csv_row(row))

    return rows