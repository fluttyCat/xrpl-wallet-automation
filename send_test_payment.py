# Backward-compatible helper script.
# You can also use: python3 xrpl_wallet_automation.py send --amount 1
from xrpl_wallet_automation import XRPL_RECEIVER, send_payment, print_json

if not XRPL_RECEIVER:
    raise RuntimeError("XRPL_RECEIVER is missing in .env")

result = send_payment(XRPL_RECEIVER, 1)
print_json(result)
print("Payment sent successfully.")
