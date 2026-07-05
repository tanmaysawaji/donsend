# Architecture Decision Records (ADRs)

An ADR captures **one significant decision**: the context, what we chose, and the
consequences. It's a lightweight habit that pays off in two ways here — it forces
you to think a decision through, and it's excellent interview material ("walk me
through a technical decision you made and why").

## When to write one

Write an ADR when a choice is:
- hard or expensive to reverse later (database, auth model, framework), or
- non-obvious enough that future-you will ask "why did I do it this way?", or
- something you considered real alternatives for.

Skip it for routine, easily-reversible choices. Don't turn this into ceremony.

## How

1. Copy `0000-template.md` to `NNNN-short-title.md` (next number, zero-padded).
2. Fill it in. Keep it to one page.
3. Set status to `Accepted` once decided. If a later ADR overturns it, mark this
   one `Superseded by ADR-XXXX` rather than deleting it — the history is the point.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-jwt-storage.md) | Store the JWT refresh token in an httpOnly cookie | Accepted |
| [0003](0003-websocket-auth.md) | Authenticate WebSocket connections with a short-lived ticket | Accepted |
| [0004](0004-v1-database-schema.md) | V1 database schema — users, invite codes, friendships, messages | Accepted |

> Add a row per ADR. The first ADR below is the conventional "we will use ADRs" record.
