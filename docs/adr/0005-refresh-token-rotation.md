# ADR-0005: Refresh token rotation via a single-session table

- **Status:** Accepted
- **Date:** 2026-07-08

## Context

`CLAUDE.md` commits to "short-lived access token + refresh token rotation."
ADR-0002 decided *where the browser stores* the refresh token (an httpOnly
cookie), but not *how the server tracks it* — and rotation specifically
requires server-side state: a pure stateless JWT gives the server no way to
know whether a given refresh token has already been used and replaced by a
newer one.

This also raises a question ADR-0002 never addressed: should a user be able
to be logged in on multiple devices/browsers at once? Supporting that
requires tracking many valid refresh tokens per user; not supporting it
needs only one.

## Decision

**One active session per user.** A new `sessions` table has `user_id` as its
primary key (not a separate surrogate id), which makes "at most one row per
user" a schema-level guarantee rather than an application convention.
Logging in again — from any device — overwrites this row.

| column | type | notes |
|---|---|---|
| `user_id` | `BIGINT`, PK, FK → `users.id` | |
| `refresh_token_hash` | `VARCHAR`, `UNIQUE` | SHA-256 hash, not the raw token |
| `expires_at` | `TIMESTAMPTZ NOT NULL` | |
| `created_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | set on every rotation |

**Access and refresh tokens are shaped differently, on purpose:**

- The **access token is a JWT** — self-contained and stateless, carrying the
  user's identity and an expiry, signed with our secret key. It's verified
  on every API request purely by checking the signature, with no database
  round-trip, because it's used *frequently*.
- The **refresh token is a plain opaque random string**
  (`secrets.token_urlsafe`), not a JWT. It's used *rarely* (only when the
  access token has expired), so a database lookup on each use is cheap. The
  server hashes the presented token and looks up `sessions` directly by
  `WHERE refresh_token_hash = :hash` — the `UNIQUE` index makes this a direct
  lookup without needing to already know which user it belongs to.

Refreshing means: hash the presented token → find the matching `sessions`
row → check `expires_at` → issue a new access token and a new refresh token
→ overwrite the row with the new hash. An old, already-rotated-out refresh
token simply matches no row anymore — rotation is enforced by the overwrite
itself, not a separate revocation check.

**Hashing uses SHA-256, not Argon2.** Argon2's slowness/memory-hardness
exists specifically to resist *guessing* attacks against low-entropy,
human-chosen passwords. A refresh token is already a high-entropy random
value that isn't guessable — hashing it with Argon2 would only add cost with
no corresponding security benefit. A fast cryptographic hash is the correct
tool for "detect whether the DB row's hash matches this known value."

## Alternatives considered

- **Refresh token also a JWT** (e.g. carrying `sub` and a `jti` claim) —
  rejected as unnecessary complexity. Since we already need a DB row per
  session to support rotation, the row itself can be looked up directly by a
  hash of an opaque token; there's no benefit to also making that token
  self-describing and signed.

- **Multiple concurrent sessions** (a real `refresh_tokens` table, one row
  per issued token, with revocation/rotation-chain tracking) — would support
  being logged in on a phone and a laptop simultaneously, and a "logout"
  that only kills one session. Rejected for V1: nothing in
  `docs/requirements/v1.md` asks for multi-device support, and building
  that tracking now would be exactly the kind of speculative infrastructure
  `CLAUDE.md` says to avoid. Revisit if multi-device becomes a real
  requirement — the migration path from a single `user_id`-keyed row to a
  proper multi-row table is straightforward.

- **Argon2 for the refresh token hash** (for consistency with password
  hashing) — rejected; see reasoning above. Using a slow hash here would
  add real latency to every token refresh for no security benefit.

## Consequences

- A user logging in on a second device silently invalidates their first
  device's session — there is no warning or explicit sign-out of the other
  session. Acceptable for V1's scope; worth surfacing to users explicitly if
  multi-device support is ever added later.
- "Logout" is simply deleting the user's `sessions` row (or letting it
  expire) — there's no separate revocation list to maintain.
- Verifying an access token never touches the database; verifying/rotating
  a refresh token always does. This asymmetry is intentional and matches
  how often each operation happens.
