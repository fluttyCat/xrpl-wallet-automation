# XRPL Wallet Automation & AI Risk Review

For this proof-of-work, I built a small XRPL automation project that covers three wallet-style features: balance checks, transaction history, and payment flows.

The system can check a Testnet wallet balance, send a Testnet XRP payment, export transaction history, and generate a short AI/fallback review note for successful payments.

## What the workflow does

1. Checks the wallet balance using the XRPL API.
2. Sends a test payment from one Testnet wallet to another.
3. Fetches validated transaction history.
4. Filters successful Payment transactions.
5. Saves the transaction data into CSV files.
6. Creates an AI or fallback review summary.
7. Logs failed API or AI calls into a dead-letter file.

## Why I designed it this way

The main rule is to save useful data before calling slow or unreliable external services.

That way, if OpenAI, a CRM, or another API fails, the transaction data is still stored and can be retried later.

## Stack

- Python
- XRP Ledger API
- XRPL Testnet
- xrpl-py
- OpenAI API optional
- CSV output
- Retry and dead-letter pattern

## Result

The project successfully sent a Testnet XRP payment, exported the transaction history, and processed the payment into a review-ready CSV.

For a small benchmark, reviewing 10 transactions manually would take around 30 minutes if each transaction takes about 3 minutes to check. With the automation, each transaction can be normalized and summarized in about 30 seconds after detection.

Estimated review-time reduction: around 83%.
