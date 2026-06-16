# XRPL Wallet Automation & AI Risk Review

This is a proof-of-work project for an AI Automation Specialist evaluation.

It demonstrates a small but real XRP Ledger automation system with:

- transaction history
- balance checks
- Testnet payment flow
- AI/fallback transaction review summary
- retry logic
- dead-letter error logging

The project is intentionally simple to run and easy for a tester/reviewer to verify.

## Features

### 1. Balance Check

Checks the XRP balance of a Testnet wallet.

```bash
python3 xrpl_wallet_automation.py balance
```

Output:

```text
output/balance_check.csv
```

### 2. Transaction History

Fetches validated transactions for a wallet.

```bash
python3 xrpl_wallet_automation.py history
```

Output:

```text
output/transaction_history.csv
```

### 3. Payment Flow

Sends a Testnet XRP payment from the sender wallet to the receiver wallet.

```bash
python3 xrpl_wallet_automation.py send --amount 1
```

Output:

```text
output/payment_flows.csv
```

### 4. AI Transaction Monitoring

Filters successful Payment transactions and creates an AI or fallback operations summary.

```bash
python3 xrpl_wallet_automation.py monitor
```

Output:

```text
output/processed_transactions.csv
```

If `OPENAI_API_KEY` is empty, the project still works and creates a local fallback summary.

---

## Tech Stack

- Python
- XRP Ledger API
- XRPL Testnet
- xrpl-py
- OpenAI API optional
- CSV output
- Retry and dead-letter pattern

---

## Project Structure

```text
.
├── xrpl_wallet_automation.py
├── xrpl_monitor.py
├── send_test_payment.py
├── requirements.txt
├── .env.example
├── output/
│   ├── balance_check.csv
│   ├── transaction_history.csv
│   ├── payment_flows.csv
│   ├── processed_transactions.csv
│   └── dead_letter.csv
├── docs/
│   ├── xrpl_feature_mapping.md
│   ├── case_study_human.md
│   ├── error_handling.md
│   ├── timeout_fix.md
│   └── loom_script.md
└── diagrams/
    ├── error_handling.mmd
    └── timeout_fix.mmd
```

---

## Setup

### 1. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env`

```bash
cp .env.example .env
```

Edit `.env`:

```env
XRPL_ACCOUNT=your_sender_testnet_address
XRPL_RPC_URL=https://s.altnet.rippletest.net:51234/
XRPL_SECRET=your_sender_testnet_secret
XRPL_RECEIVER=your_receiver_testnet_address

OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
XRPL_LIMIT=50
```

Important: do not share or commit `.env`. Even on Testnet, keep `XRPL_SECRET` private.

---

## Recommended Test Flow

Run these commands in order:

### 1. Check balance

```bash
python3 xrpl_wallet_automation.py balance
```

### 2. Send test payment

```bash
python3 xrpl_wallet_automation.py send --amount 1
```

### 3. Export transaction history

```bash
python3 xrpl_wallet_automation.py history
```

### 4. Process payments with AI/fallback summary

```bash
python3 xrpl_wallet_automation.py monitor
```

### 5. Check output files

```bash
ls output
cat output/balance_check.csv
cat output/transaction_history.csv
cat output/payment_flows.csv
cat output/processed_transactions.csv
```

---

## Expected Output

After a successful test, the `output/` folder should contain CSV files like:

```text
balance_check.csv
transaction_history.csv
payment_flows.csv
processed_transactions.csv
```

A successful payment result should include:

```text
tesSUCCESS
```

---

## Error Handling

The project uses a simple production-style rule:

```text
Save useful data before slow or unreliable external steps.
```

Failure paths include:

```text
XRPL timeout → retry
Rate limit → wait and retry
Server error → retry with backoff
OpenAI failure → fallback summary + dead-letter log
Permanent failure → output/dead_letter.csv
```

---

## Common Issues

### `No successful Payment transactions found`

The wallet probably has no recent successful payments.

Run:

```bash
python3 xrpl_wallet_automation.py send --amount 1
python3 xrpl_wallet_automation.py monitor
```

### `ModuleNotFoundError: No module named 'xrpl'`

Install dependencies again:

```bash
pip install -r requirements.txt
```

### `actNotFound: Account not found`

Usually means one of these:

- wallet is not funded
- secret does not match sender address
- using Mainnet RPC with a Testnet wallet

Make sure `.env` uses:

```env
XRPL_RPC_URL=https://s.altnet.rippletest.net:51234/
```

---

## Proof-of-Work Screenshot Checklist

For evaluation, capture:

1. terminal output from `balance`
2. terminal output from `send`
3. terminal output from `history`
4. terminal output from `monitor`
5. CSV output files
6. `docs/error_handling.md`
7. `docs/timeout_fix.md`
8. diagrams from `diagrams/`

---

## Notes

This project is built on XRPL Testnet only.

Do not use real funds or Mainnet secrets for this proof-of-work.
