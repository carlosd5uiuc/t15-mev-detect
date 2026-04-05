import csv
from dataclasses import dataclass

@dataclass
class TransactionRow:
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

    @classmethod
    def from_csv_row(cls, row: dict) -> "TransactionRow":
        return cls(
            timestamp=int(row["timestamp_ms"]),
            hash=row["hash"],
            chainId=row["chain_id"],
            from_address=row["from"],   # "from" is a Python keyword
            to=row["to"],
            value=row["value"],
            nonce=row["nonce"],
            gas=row["gas"],
            gasPrice=row["gas_price"],
            gasTipCap=row["gas_tip_cap"],
            gasFeeCap=row["gas_fee_cap"],
            dataSize=int(row["data_size"]),
            data4Bytes=row["data_4bytes"],
        )
    
def load_transactions(file="2026-03-01-100k.csv"):
    rows = []
    with open(f"data/{file}", "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # skips header row
        next(reader)

        for row in reader:
            rows.append(TransactionRow.from_csv_row(row))
    return rows
