# Error Handling Architecture

The workflow is designed around one rule:

**Save the data before calling AI or external systems.**

External APIs can fail. OpenAI can timeout. A CRM can reject a request. Public blockchain APIs can also have temporary failures.

## Logic

1. Call XRPL API.
2. Validate the response.
3. Save useful data into CSV.
4. Run AI/fallback summary.
5. If the AI call fails, save a fallback summary.
6. If an API call fails after retries, save the error to `output/dead_letter.csv`.

## Failure paths

```text
XRPL API timeout → retry with backoff
Rate limit → wait and retry
Server error → retry with backoff
Invalid response → save to dead-letter
OpenAI failure → fallback summary + dead-letter log
```

## Why this prevents data loss

The important transaction data is saved before slow or unreliable steps.

So even if OpenAI or another service fails, the transaction can still be reviewed or retried later.
