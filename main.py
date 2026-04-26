import argparse

from blockchain_fetcher import BlockchainFetcher
from mev_types.arbitrage import calculate_arbitrage
from mev_types.frontrun import detect_front_running
from mev_types.sandwich import detect_sandwich_attacks

def print_arbitrage_table(rows: list[dict], block_number: int | None = None) -> None:
    if not rows:
        print("No arbitrage results found.")
        return

    headers = ["Tx", "Address", "Token", "Value"]
    if block_number is not None:
        headers.insert(1, "Block")

    table_rows = []
    for row in rows:
        current_row = [
            row["tx"],
            row["address"],
            row["token"],
            f'{row["value"]:.6f}',
        ]
        if block_number is not None:
            current_row.insert(1, str(block_number))
        table_rows.append(current_row)

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
    parser = argparse.ArgumentParser(
        description="Fetch blockchain data by block or transaction"
    )

    mev_subparsers = parser.add_subparsers(dest="mev_type", required=True)

    arbitrage_parser = mev_subparsers.add_parser("arbitrage", help="Arbitrage mode")
    arbitrage_subparsers = arbitrage_parser.add_subparsers(dest="command", required=True)

    block_parser = arbitrage_subparsers.add_parser("block", help="Fetch by block number")
    block_parser.add_argument("id", type=int, help="Block number")

    tx_parser = arbitrage_subparsers.add_parser("tx", help="Fetch by transaction hash")
    tx_parser.add_argument("id", type=str, help="Transaction hash")

    sandwich_parser = mev_subparsers.add_parser("sandwich", help="Sandwich mode")
    sandwich_parser.add_argument("id", type=int, help="Block number")

    frontrun_parser = mev_subparsers.add_parser("frontrun", help="Frontrun mode")
    frontrun_parser.add_argument("id", type=int, help="Block number")

    return parser.parse_args()

def main() -> None:
    args = parse_args()
    client = BlockchainFetcher()

    if args.mev_type == "arbitrage":
        if args.command == "tx":
            transfers = client.fetch_transfer_by_tx(args.id)
            arbitrage_result = calculate_arbitrage(transfers)
            table_data = []
            for item in arbitrage_result:
                table_data.append({
                    "tx": args.id,
                    "address": item["address"],
                    "token": item["token"],
                    "value": item["value"],
                })

            print_arbitrage_table(table_data)

        elif args.command == "block":
            tx_transfers = client.fetch_transfers_by_block_from_cache(args.id)

            table_data = []

            for tx_hash, transfers in tx_transfers.items():
                result = calculate_arbitrage(transfers)

                if len(result):
                    for item in result:
                        table_data.append({
                            "tx": tx_hash,
                            "address": item["address"],
                            "token": item["token"],
                            "value": item["value"],
                        })

            print_arbitrage_table(table_data, args.id)
    
    elif args.mev_type == "frontrun":
        txs = client.fetch_local_transactions(args.id)
        result = detect_front_running(txs)
        print(result)
    
    elif args.mev_type == "api-frontrun":
        txs = client.fetch_block_transactions(args.id)
        result = detect_front_running(txs)
        print(result)
    
    elif args.mev_type == "sandwich":
        txs = client.fetch_local_transactions(args.id)
        result = detect_sandwich_attacks(txs)
        print(result)
    
if __name__ == "__main__":
    main()
