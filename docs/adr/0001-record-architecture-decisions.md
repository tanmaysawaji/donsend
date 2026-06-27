# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-06-18

## Context

This is a learning project with an explicit goal of practising a professional
software development lifecycle. Decisions made along the way (stack, auth model,
data model, deployment) should be traceable, both so future-me understands the
"why" and so they can be discussed in interviews.

## Decision

We will use Architecture Decision Records, stored in `docs/adr/`, one Markdown
file per significant decision, following the template in `0000-template.md`.

## Alternatives considered

- **No formal record** — rely on commit messages and memory. Rejected: the "why"
  behind a decision is exactly what gets lost, and it's the most valuable part.
- **A single running design doc** — one growing file. Rejected: harder to see when
  and why individual decisions changed; ADRs give a clean, dated history.

## Consequences

- A small, recurring habit: each meaningful decision costs ~10 minutes to record.
- A clear decision history that doubles as interview prep.
- Risk of over-documenting trivial choices — mitigated by the "when to write one"
  guidance in `README.md`.
