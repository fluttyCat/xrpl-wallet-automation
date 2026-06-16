# Loom Walkthrough Script

Hi Shem, this is my proof-of-work walkthrough.

I built a small XRPL wallet automation project. It covers balance checks, transaction history, payment flows, and AI/fallback transaction review.

First, I run the balance command to check the Testnet wallet balance.

Then I send a Testnet XRP payment from the sender wallet to the receiver wallet.

After that, I export the transaction history using the XRPL API. The transaction history is saved into a CSV file so it can be checked easily.

Then I run the monitor command. This filters successful Payment transactions and creates a short operations review note. If there is no OpenAI API key, the system still works by creating a fallback summary.

For error handling, I added retries for temporary API failures, delay for rate-limit situations, and a dead-letter file for failures that should be reviewed later.

The main design decision is that useful data should be saved before calling AI or other external systems. That way, even if OpenAI or a CRM fails, the original transaction data is not lost.
