# XRPL Feature Mapping

This project implements common XRPL wallet/product features in a small automation system.

## 1. Transaction history

Implemented with:

```bash
python3 xrpl_wallet_automation.py history
```

What it does:

- Calls XRPL `account_tx`
- Fetches validated transactions for the configured wallet
- Exports transaction history to `output/transaction_history.csv`

## 2. Balance checks

Implemented with:

```bash
python3 xrpl_wallet_automation.py balance
```

What it does:

- Calls XRPL `account_info`
- Reads the XRP balance from account data
- Saves the balance check to `output/balance_check.csv`

## 3. Payment flows

Implemented with:

```bash
python3 xrpl_wallet_automation.py send --amount 1
```

What it does:

- Creates an XRP Payment transaction
- Autofills transaction fields
- Signs locally using the Testnet wallet secret
- Submits and waits for validation
- Saves the payment result to `output/payment_flows.csv`

## 4. AI-assisted monitoring

Implemented with:

```bash
python3 xrpl_wallet_automation.py monitor
```

What it does:

- Fetches transaction history
- Filters successful Payment transactions
- Saves processed payments
- Creates an AI or fallback review summary
- Saves results to `output/processed_transactions.csv`

## Why this is useful for the REWORK proof

This shows a real automation system around a financial/blockchain API:

- API integration
- transaction history
- balance checking
- payment automation
- async-safe processing mindset
- retry/error handling
- dead-letter logging
- AI-assisted review
