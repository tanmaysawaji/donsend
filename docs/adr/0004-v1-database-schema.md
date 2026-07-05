# ADR-0004: V1 database schema — users, invite codes, friendships, messages

- **Status:** Accepted
- **Date:** 2026-07-04

## Context

V1 needs four entities: users (with a separate login identity and display
handle), single-use invite codes, mutual friendships with accept/reject, and
persisted 1:1 text messages. Several parts of this have real trade-offs worth
recording: how to model a friendship's lifecycle, what a rejection means,
primary key strategy, and whether message content should be encrypted at
rest.

## Decision

**Tables:** `users`, `invite_codes`, `friendships`, `messages`. All primary
keys are `BIGINT` identity (auto-increment) columns.

**`friendships` is a single table, not `friend_requests` + `friendships`.**
One row per unordered pair of users, with a `status` column
(`pending` / `accepted` / `rejected`) that transitions in place:

- `user_a_id` / `user_b_id` — the pair, always stored with
  `user_a_id < user_b_id` (app-enforced ordering), with
  `UNIQUE (user_a_id, user_b_id)` and `CHECK (user_a_id < user_b_id)`. This
  makes "one relationship per pair, ever" a DB-level guarantee instead of an
  application convention — A→B and B→A collide on insert.
- `requested_by_id` — which of the two users actually sent the current
  request, kept separate from the pair ordering so "who can accept/reject"
  isn't tangled up with "which id is numerically smaller." Constrained to
  equal one of the two pair members.
- **Rejection does not delete the row.** A rejected friendship stays as a
  `rejected` row. A later request from either side is an `UPDATE` (flip back
  to `pending`, set `requested_by_id` to the new sender, clear
  `responded_at`) rather than an `INSERT` — the pair's row is a permanent
  slot for that relationship, not a disposable event.

**Message content is stored as plain text, no application-level
encryption**, capped at 4,000 characters (`VARCHAR(4000)`). See discussion
below.

## Alternatives considered

- **Separate `friend_requests` and `friendships` tables** — rejected because
  accept/reject becomes a delete-from-one-table-plus-insert-into-another
  operation for what is conceptually one row changing state. A single table
  keeps the transition atomic and avoids the two tables drifting out of sync.

- **Deleting the row on rejection** — simpler in one sense (a re-request is
  always a plain `INSERT`, no existing-row check needed), but it throws away
  the pair's "slot," so a re-request needs to check for an existing rejected
  row and `UPDATE` it anyway to avoid violating the pair uniqueness — deleting
  doesn't actually remove that branch, it just removes the row you'd want to
  reuse. Keeping the row was chosen so the pair's row is created exactly once
  and every subsequent action against it is an `UPDATE`.

- **UUID primary keys** — considered for non-guessable IDs. Rejected for V1:
  `BIGINT` identity is smaller, indexes faster, and gives free insertion-order
  semantics that keyset pagination on `messages` can use directly. Sequential
  IDs leaking rough row counts is not a meaningful risk for a private,
  invite-only chat app at this scale. Worth revisiting only if IDs are ever
  exposed somewhere they shouldn't be guessable (they currently aren't).

- **Native Postgres `ENUM` type for `friendships.status`** — rejected in
  favor of a plain `VARCHAR` with a `CHECK` constraint. A native enum
  requires `ALTER TYPE ... ADD VALUE` (which can't run inside a normal
  transaction in older Postgres versions) to add a new status later; a
  `CHECK` constraint is a plain migration. Application-level type safety is
  still enforced via a Python `enum.Enum` mapped through SQLAlchemy.

- **Per-user application-level encryption key for `messages.content`** —
  considered and rejected. The key would necessarily live in the same
  database (and the same backups) as the ciphertext it protects, so it
  defends against nothing: any attacker who can read the `messages` table can
  also read the key. Encryption only protects data from an attacker who has
  the ciphertext but not the key — this scheme fails that test entirely.
  Meaningful alternatives protect different threats and weren't pursued
  because they're already out of scope: full-disk/Postgres-level encryption
  (protects backups/disk theft, is an infra concern not a schema concern) and
  real end-to-end encryption (protects against a compromised or curious
  server operator, but is explicitly deferred — see `docs/requirements/v1.md`,
  V1 is TLS-in-transit only).

- **Unbounded `TEXT` for `messages.content`** — rejected in favor of a
  4,000-character cap. In Postgres, `TEXT` and `VARCHAR(n)` are stored
  identically (no performance cost to capping), so an unbounded column buys
  nothing except letting a buggy or malicious client store arbitrarily large
  rows. 4,000 characters is comfortably beyond normal chat use (in the same
  ballpark as Telegram's 4,096-character limit) while ruling out pathological
  inputs. A tighter 2,000-character cap was also considered and rejected as
  needlessly conservative for no real benefit. This DB-level cap is a
  backstop, not the primary UX validation — the messaging API's request
  schema should also validate length so users get a friendly error before
  ever reaching this constraint.

## Consequences

- Sending a friend request always needs a "does a row exist for this pair"
  check before deciding `INSERT` vs `UPDATE` — there is no code path that
  blindly inserts.
- No `conversations` table exists yet. Message history for a 1:1 pair is
  queried directly by `(sender_id, recipient_id)` in either order. Adding
  group chat later will require introducing this table and backfilling
  `messages` with a `conversation_id` — deferred deliberately per
  `docs/requirements/v1.md`.
- Message content is readable by anyone with database access (the app, an
  admin with `psql` access, or anyone who obtains a DB backup). This matches
  the documented V1 scope (TLS-only) but should be called out explicitly to
  anyone reasoning about this app's privacy properties.
- IDs are sequential and predictable. Nothing in V1 exposes another user's
  row count or relative signup/message order in a way that matters, but this
  should be reconsidered if that changes.
