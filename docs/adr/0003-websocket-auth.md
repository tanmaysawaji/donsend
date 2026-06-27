# ADR-0003: Authenticate WebSocket connections with a short-lived ticket

- **Status:** Accepted
- **Date:** 2026-06-27

## Context

The chat feature uses a persistent WebSocket connection. Every connection must
be authenticated — we need to know which user is on the other end.

HTTP requests are easy to authenticate: send the access token in the
`Authorization` header. WebSocket upgrades are harder because:

1. Browser WebSocket APIs do not allow setting custom headers on the initial
   upgrade request.
2. Our refresh token lives in an httpOnly cookie (see ADR-0002). The access
   token lives in memory. Neither is straightforwardly available at WS
   upgrade time without some extra step.

## Decision

We use a short-lived WS ticket:

1. Before opening the WebSocket, the client calls a REST endpoint
   (`POST /auth/ws-ticket`) with its access token in the `Authorization`
   header.
2. The server validates the access token and returns a one-time ticket (a
   random token stored in-memory or in the DB) with a short TTL (~30 seconds).
3. The client opens the WebSocket and sends the ticket as a query parameter:
   `wss://host/ws?ticket=<token>`.
4. The server validates the ticket on upgrade, associates the connection with
   the user, and invalidates the ticket immediately (one-time use).

## Alternatives considered

- **JWT in the first WS message** — client opens the connection, then sends
  the access JWT as the first message. Simpler, but it mixes auth logic into
  the message handler: every incoming message handler must guard against
  receiving non-auth messages before auth is complete. It also leaves a window
  where an unauthenticated connection is open. Rejected for cleanliness.

- **Cookie-based (browser sends httpOnly cookie on upgrade)** — browsers do
  send cookies on WS upgrade requests if the URL is same-origin. This would
  work with our httpOnly cookie setup and requires no extra endpoint. Rejected
  because it ties WS auth tightly to the cookie mechanism; if we ever move to
  a mobile client or a different auth scheme, this stops working. The ticket
  approach is more explicit and portable.

- **Query parameter with the access JWT** — send the JWT directly in the URL:
  `wss://host/ws?token=<jwt>`. Simple, but JWTs in URLs appear in server logs,
  browser history, and proxy logs. A short-lived opaque ticket in the URL is
  far less damaging if it leaks. Rejected.

## Consequences

- A small extra HTTP round-trip is required before every WS connection. In
  practice this is negligible — it happens once per session.
- The server needs a ticket store (a simple in-memory dict or a DB table with
  a TTL is sufficient for V1).
- The 30-second TTL means a ticket obtained and not used within 30 seconds
  is rejected — the client must request a fresh one. This is an acceptable
  constraint.
- Auth stays entirely in HTTP; the WS handler only checks a ticket. This keeps
  the WebSocket layer simple and easy to test independently.
