Cinema Ticket System — In-Memory (Flipkart Machine Coding)

Clean, modular, in-memory implementation of a cinema ticketing system designed for machine-coding rounds.
Includes per-show concurrency locks, a mini scheduler that auto-starts shows at start_time, a CLI, and a full pytest suite (including race tests).

✨ Features

Register/start/end shows; update price only before start

Order tickets (batch only) with cheapest-show selection (tie → earliest registered)

Cancel entire booking (no partial):

Before start: seats restored, 50% refund

After start / ended: no refund, no seat restore

Exact string match for movie names (no fuzzy matching)

Single city, single seat type (per spec simplifications)

Concurrency: safe under concurrent booking/cancellation using per-show locks

Scheduler: auto-starts shows at their configured start_time (best-effort)

Clean layering: models → repo → services → cli, with utils helpers