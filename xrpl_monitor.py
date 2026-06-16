# Backward-compatible helper script.
# You can also use: python3 xrpl_wallet_automation.py monitor
from xrpl_wallet_automation import XRPL_ACCOUNT, XRPL_LIMIT, monitor_payments

if not XRPL_ACCOUNT:
    raise RuntimeError("XRPL_ACCOUNT is missing in .env")

print(f"Fetching recent XRPL transactions for: {XRPL_ACCOUNT}")
rows = monitor_payments(XRPL_ACCOUNT, XRPL_LIMIT)

if not rows:
    print("No successful Payment transactions found in the latest result.")
else:
    print(f"Found {len(rows)} successful payment transaction(s).")
    print("Done. Check: output/processed_transactions.csv")
