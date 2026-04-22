import argparse

from blockchain_fetcher import BlockchainFetcher
from mev_types.arbitrage import calculate_arbitrage

def print_arbitrage_table(rows: list[dict], block_number: int) -> None:
    if not rows:
        print("No arbitrage results found.")
        return

    headers = ["Tx", "Block", "Address", "Token", "Value"]

    table_rows = []
    for row in rows:
        table_rows.append([
            row["tx"],
            str(block_number),
            row["address"],
            row["token"],
            f'{row["value"]:.6f}',
        ])

    col_widths = [
        max(len(headers[i]), max(len(r[i]) for r in table_rows))
        for i in range(len(headers))
    ]

    def format_row(row):
        return " | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row))

    separator = "-+-".join("-" * width for width in col_widths)

    print(format_row(headers))
    print(separator)
    for row in table_rows:
        print(format_row(row))

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch blockchain data by block or transaction")
    subparsers = parser.add_subparsers(dest="command", required=True)

    block_parser = subparsers.add_parser("block", help="Fetch by block number")
    block_parser.add_argument("id", type=int, help="Block number")

    block_parser.add_argument("start", type=int, help="Start tx index (inclusive)")
    block_parser.add_argument("end", type=int, help="End tx index (exclusive)")

    tx_parser = subparsers.add_parser("tx", help="Fetch by transaction hash")
    tx_parser.add_argument("id", type=str, help="Transaction hash")

    return parser.parse_args()

def main() -> None:
    args = parse_args()
    client = BlockchainFetcher()

    if args.command == "tx":
        transfers = client.fetch_transfer_by_tx(args.id)
        arbitrage_result = calculate_arbitrage(transfers)
        print(arbitrage_result)

    elif args.command == "block":
        txs = client.fetch_block_transactions(args.id)

        selected_txs = txs[args.start:args.end]
        table_data = []
        for tx in selected_txs:
            transfers = client.fetch_transfer_by_tx(tx.tx_hash)
            result = calculate_arbitrage(transfers)

            if len(result):
                for item in result:
                    table_data.append({
                        "tx": tx.tx_hash,
                        "address": item["address"],
                        "token": item["token"],
                        "value": item["value"],
                    })

        print_arbitrage_table(table_data, args.id)
    
if __name__ == "__main__":
    main()
