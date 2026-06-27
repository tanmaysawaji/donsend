# Iteration Requirements — TEMPLATE

Copy this to `vN.md` (e.g. `v1.md`) per iteration. Keep it to roughly one page.
The job of this doc is to make scope explicit *before* code is written.

---

## Iteration: vN — <one-line name>

- **Status:** Draft | Active | Done
- **Goal (one sentence):** What does this iteration prove or deliver?

## In scope

The smallest set of capabilities that makes this iteration worth shipping.

- ...

## Explicitly out of scope

Naming what you are *not* doing is what keeps scope creep out.

- ...

## Acceptance criteria

Observable, checkable statements. "Done" = all of these are true.

- [ ] ...
- [ ] ...

## Open decisions

Decisions this iteration forces. Resolve each (an ADR if it's significant)
before or early in the work — don't let them get decided by accident.

- [ ] ...

## Notes / risks

Anything worth remembering: known unknowns, things deferred, gotchas.

---

<!--
When you draft v1.md, these are the open decisions we already identified and
should resolve up front:

- Username vs email vs display name: is the username the login identity or just a
  handle? Is it immutable? Case-sensitive? (Uniqueness is a real DB constraint.)
- Friendship model: mutual with accept/reject requests (Facebook-style) or
  one-directional follow (Twitter-style)? Mutual-with-requests is the natural fit
  for chat.
- Message delivery semantics: online-only delivery, or persisted and shown on
  next login? Persisting is simpler to reason about and more realistic.
- Registration gating mechanism: env flag + seed script (simplest) vs invite
  codes (more work, real feature) vs reverse-proxy basic auth (crude, zero code).
-->
