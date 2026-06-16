# Timeout Fix: Webhook → OpenAI → HubSpot

The problem is that OpenAI is inside the live webhook request.

If OpenAI takes more than 30 seconds, the webhook can timeout and the lead can be lost.

I would redesign the flow like this:

```text
Webhook receives lead
↓
Save raw lead immediately with status = PENDING
↓
Return 200 OK quickly
↓
Push job to queue/background worker
↓
Worker calls OpenAI scoring
↓
Success?
├─ Yes
│  ├─ Save AI score
│  ├─ Send/update HubSpot
│  └─ Mark lead as COMPLETED
│
└─ No
   ├─ Timeout → retry with exponential backoff
   ├─ Rate limit → wait and retry
   └─ Failed after retries → move to dead-letter queue + alert
```

## Main idea

I would remove OpenAI from the synchronous webhook request.

The webhook should only validate and save the lead, then return success immediately.

AI scoring and HubSpot updates should happen asynchronously through a queue, worker, or secondary trigger.

This way, no lead is lost even if OpenAI is slow or HubSpot fails.
