import argparse
import csv
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    from xrpl.clients import JsonRpcClient
    from xrpl.wallet import Wallet
    from xrpl.models.transactions import Payment
    from xrpl.transaction import autofill, sign, submit_and_wait
    from xrpl.utils import xrp_to_drops
except Exception:
    JsonRpcClient = None
    Wallet = None
    Payment = None
    autofill = None
    sign = None
    submit_and_wait = None
    xrp_to_drops = None

load_dotenv()

XRPL_RPC_URL = os.getenv("XRPL_RPC_URL", "https://s.altnet.rippletest.net:51234/")
XRPL_ACCOUNT = os.getenv("XRPL_ACCOUNT", "")
XRPL_SECRET = os.getenv("XRPL_SECRET", "")
XRPL_RECEIVER = os.getenv("XRPL_RECEIVER", "")
XRPL_LIMIT = int(os.getenv("XRPL_LIMIT", "50"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

BALANCE_CSV = OUTPUT_DIR / "balance_check.csv"
HISTORY_CSV = OUTPUT_DIR / "transaction_history.csv"
PAYMENTS_CSV = OUTPUT_DIR / "payment_flows.csv"
MONITOR_CSV = OUTPUT_DIR / "processed_transactions.csv"
DEAD_LETTER_CSV = OUTPUT_DIR / "dead_letter.csv"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_csv_row(path: Path, fieldnames: List[str], row: Dict[str, Any]) -> None:
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def dead_letter(stage: str, error: str, payload: Optional[Dict[str, Any]] = None) -> None:
    write_csv_row(
        DEAD_LETTER_CSV,
        ["created_at", "stage", "error", "payload"],
        {
            "created_at": now_iso(),
            "stage": stage,
            "error": error,
            "payload": json.dumps(payload or {}, ensure_ascii=False),
        },
    )


def rpc_request(method: str, params: List[Dict[str, Any]], retries: int = 3, timeout: int = 20) -> Dict[str, Any]:
    payload = {"method": method, "params": params}
    last_error = ""

    for attempt in range(1, retries + 1):
        try:
            response = requests.post(XRPL_RPC_URL, json=payload, timeout=timeout)

            if response.status_code == 429:
                wait_seconds = 30 * attempt
                last_error = f"Rate limited: HTTP 429. Waiting {wait_seconds}s."
                print(last_error)
                time.sleep(wait_seconds)
                continue

            if response.status_code >= 500:
                wait_seconds = 5 * attempt
                last_error = f"Server error HTTP {response.status_code}. Waiting {wait_seconds}s."
                print(last_error)
                time.sleep(wait_seconds)
                continue

            response.raise_for_status()
            data = response.json()

            if data.get("error"):
                raise RuntimeError(json.dumps(data["error"]))

            result = data.get("result", {})
            if result.get("status") == "error":
                raise RuntimeError(json.dumps(result))

            return result

        except Exception as e:
            last_error = str(e)
            print(f"[Attempt {attempt}/{retries}] {method} error: {last_error}")
            time.sleep(3 * attempt)

    dead_letter(method, last_error, payload)
    raise RuntimeError(f"{method} failed after retries: {last_error}")


def drops_to_xrp(drops: Any) -> float:
    return int(drops) / 1_000_000


def get_balance(account: str) -> Dict[str, Any]:
    """Feature 1: balance checks using account_info."""
    result = rpc_request(
        "account_info",
        [
            {
                "account": account,
                "ledger_index": "validated",
                "api_version": 2,
            }
        ],
    )

    account_data = result.get("account_data", {})
    balance_xrp = drops_to_xrp(account_data.get("Balance", "0"))

    row = {
        "checked_at": now_iso(),
        "account": account,
        "balance_xrp": balance_xrp,
        "sequence": account_data.get("Sequence", ""),
        "ledger_index": result.get("ledger_index", ""),
    }

    write_csv_row(
        BALANCE_CSV,
        ["checked_at", "account", "balance_xrp", "sequence", "ledger_index"],
        row,
    )

    return row


def fetch_transaction_history(account: str, limit: int = XRPL_LIMIT) -> List[Dict[str, Any]]:
    """Feature 2: transaction history using account_tx."""
    result = rpc_request(
        "account_tx",
        [
            {
                "account": account,
                "ledger_index_min": -1,
                "ledger_index_max": -1,
                "binary": False,
                "limit": limit,
                "forward": False,
                "api_version": 2,
            }
        ],
    )

    transactions = result.get("transactions", [])
    rows = []

    for item in transactions:
        tx = item.get("tx_json") or item.get("tx") or {}
        meta = item.get("meta") or item.get("metaData") or {}

        amount = tx.get("Amount", "") or tx.get("DeliverMax", "")
        if isinstance(amount, str) and amount.isdigit():
            amount_display = f"{drops_to_xrp(amount)} XRP"
        elif isinstance(amount, dict):
            amount_display = f"{amount.get('value')} {amount.get('currency')}"
        else:
            amount_display = str(amount)

        row = {
            "exported_at": now_iso(),
            "tx_hash": tx.get("hash", item.get("hash", "")),
            "type": tx.get("TransactionType", ""),
            "sender": tx.get("Account", ""),
            "receiver": tx.get("Destination", ""),
            "amount": amount_display,
            "destination_tag": tx.get("DestinationTag", ""),
            "ledger_index": tx.get("ledger_index", item.get("ledger_index", "")),
            "validated": item.get("validated", ""),
            "result": meta.get("TransactionResult", ""),
        }

        rows.append(row)

    for row in rows:
        write_csv_row(
            HISTORY_CSV,
            [
                "exported_at",
                "tx_hash",
                "type",
                "sender",
                "receiver",
                "amount",
                "destination_tag",
                "ledger_index",
                "validated",
                "result",
            ],
            row,
        )

    return rows


def create_local_summary(row: Dict[str, Any]) -> str:
    return (
        f"{row.get('type', 'Transaction')} detected. "
        f"Sender: {row.get('sender')}. Receiver: {row.get('receiver')}. "
        f"Amount: {row.get('amount')}. "
        f"Review note: check destination tag, amount size, and repeated sender behavior."
    )


def create_ai_summary(row: Dict[str, Any]) -> str:
    if not OPENAI_API_KEY or OpenAI is None:
        return create_local_summary(row)

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = f"""
Create a short operations review note for this XRP Ledger transaction.
Do not claim fraud. Only mention practical checks.

Transaction:
{json.dumps(row, ensure_ascii=False, indent=2)}

Output:
Summary:
Risk/Review Note:
Next Action:
"""
        response = client.responses.create(model=OPENAI_MODEL, input=prompt)
        return getattr(response, "output_text", str(response))

    except Exception as e:
        dead_letter("openai_summary", str(e), row)
        return create_local_summary(row)


def monitor_payments(account: str, limit: int = XRPL_LIMIT) -> List[Dict[str, Any]]:
    """Feature 4: AI-assisted monitoring for successful Payment transactions."""
    rows = fetch_transaction_history(account, limit=limit)
    processed = []

    for row in rows:
        if row["type"] != "Payment":
            continue
        if row["validated"] is False:
            continue
        if row["result"] and row["result"] != "tesSUCCESS":
            continue

        summary = create_ai_summary(row)

        processed_row = {
            "processed_at": now_iso(),
            "tx_hash": row["tx_hash"],
            "sender": row["sender"],
            "receiver": row["receiver"],
            "amount": row["amount"],
            "destination_tag": row["destination_tag"],
            "ledger_index": row["ledger_index"],
            "status": "COMPLETED",
            "ai_summary": summary,
        }

        write_csv_row(
            MONITOR_CSV,
            [
                "processed_at",
                "tx_hash",
                "sender",
                "receiver",
                "amount",
                "destination_tag",
                "ledger_index",
                "status",
                "ai_summary",
            ],
            processed_row,
        )

        processed.append(processed_row)

    return processed


def send_payment(receiver: str, amount_xrp: float) -> Dict[str, Any]:
    """Feature 3: payment flow using local signing and submit_and_wait."""
    if JsonRpcClient is None:
        raise RuntimeError("xrpl-py is not installed. Run: pip install xrpl-py")

    if not XRPL_SECRET:
        raise RuntimeError("XRPL_SECRET is missing in .env")

    client = JsonRpcClient(XRPL_RPC_URL)
    wallet = Wallet.from_seed(XRPL_SECRET)

    payment = Payment(
        account=wallet.classic_address,
        destination=receiver,
        amount=xrp_to_drops(amount_xrp),
    )

    prepared = autofill(payment, client)
    signed = sign(prepared, wallet)
    result = submit_and_wait(signed, client)

    response_result = result.result
    meta = response_result.get("meta", {})

    row = {
        "sent_at": now_iso(),
        "from_account": wallet.classic_address,
        "to_account": receiver,
        "amount_xrp": amount_xrp,
        "tx_hash": response_result.get("hash", ""),
        "ledger_index": response_result.get("ledger_index", ""),
        "result": meta.get("TransactionResult", ""),
        "validated": response_result.get("validated", ""),
    }

    write_csv_row(
        PAYMENTS_CSV,
        [
            "sent_at",
            "from_account",
            "to_account",
            "amount_xrp",
            "tx_hash",
            "ledger_index",
            "result",
            "validated",
        ],
        row,
    )

    return row


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="XRPL wallet automation proof-of-work: balance, history, payment, and AI monitoring."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    balance_parser = subparsers.add_parser("balance", help="Check XRP balance for XRPL_ACCOUNT.")
    balance_parser.add_argument("--account", default=XRPL_ACCOUNT)

    history_parser = subparsers.add_parser("history", help="Export transaction history.")
    history_parser.add_argument("--account", default=XRPL_ACCOUNT)
    history_parser.add_argument("--limit", type=int, default=XRPL_LIMIT)

    send_parser = subparsers.add_parser("send", help="Send a Testnet XRP payment.")
    send_parser.add_argument("--to", default=XRPL_RECEIVER)
    send_parser.add_argument("--amount", type=float, default=1.0)

    monitor_parser = subparsers.add_parser("monitor", help="Monitor payments and create AI/fallback summaries.")
    monitor_parser.add_argument("--account", default=XRPL_ACCOUNT)
    monitor_parser.add_argument("--limit", type=int, default=XRPL_LIMIT)

    args = parser.parse_args()

    if args.command == "balance":
        if not args.account:
            raise RuntimeError("Missing account. Add XRPL_ACCOUNT to .env or pass --account.")
        row = get_balance(args.account)
        print_json(row)
        print(f"Saved to {BALANCE_CSV}")

    elif args.command == "history":
        if not args.account:
            raise RuntimeError("Missing account. Add XRPL_ACCOUNT to .env or pass --account.")
        rows = fetch_transaction_history(args.account, args.limit)
        print(f"Exported {len(rows)} transaction(s).")
        print(f"Saved to {HISTORY_CSV}")

    elif args.command == "send":
        if not args.to:
            raise RuntimeError("Missing receiver. Add XRPL_RECEIVER to .env or pass --to.")
        row = send_payment(args.to, args.amount)
        print_json(row)
        print(f"Saved to {PAYMENTS_CSV}")

    elif args.command == "monitor":
        if not args.account:
            raise RuntimeError("Missing account. Add XRPL_ACCOUNT to .env or pass --account.")
        rows = monitor_payments(args.account, args.limit)
        print(f"Processed {len(rows)} successful payment transaction(s).")
        print(f"Saved to {MONITOR_CSV}")


if __name__ == "__main__":
    main()
