# ADR-0002: Store the JWT refresh token in an httpOnly cookie

- **Status:** Accepted
- **Date:** 2026-06-27

## Context

The auth system issues two tokens: a short-lived access token (used to
authenticate API requests) and a long-lived refresh token (used to get a new
access token when the old one expires). The refresh token is the sensitive one
— if an attacker steals it, they can impersonate the user indefinitely until
it is revoked.

We need to decide where the browser stores the refresh token. The choice
affects what attack surface we expose.

## Decision

The server issues the refresh token via a `Set-Cookie` response header with
the `HttpOnly` and `Secure` flags set. The browser stores and sends it
automatically; JavaScript never has access to it.

The access token is short-lived (e.g. 15 minutes) and can be held in memory
(a React state variable or module-level variable) — it is never written to
`localStorage` or `sessionStorage`.

## Alternatives considered

- **localStorage** — simple to implement: `localStorage.setItem('token', ...)`.
  Rejected because any XSS vulnerability (a malicious script injected into the
  page) can read `localStorage` and exfiltrate the token. Since the refresh
  token is long-lived, this is a serious exposure.

- **sessionStorage** — same as localStorage for XSS purposes. Also lost on tab
  close, which hurts UX. Rejected for the same reason.

- **httpOnly cookie (chosen)** — the browser sends the cookie automatically on
  matching requests, but `document.cookie` cannot read it. An XSS attack cannot
  steal what JavaScript cannot see. The trade-off is that cookies require CSRF
  protection (we will use the `SameSite=Strict` attribute, which blocks
  cross-site requests from sending the cookie automatically, covering the
  common CSRF case).

## Consequences

- The refresh token is not readable by JavaScript — XSS cannot steal it.
- `SameSite=Strict` on the cookie handles CSRF for browser-initiated requests;
  no separate CSRF token needed for V1.
- The backend must set `Set-Cookie` with `HttpOnly; Secure; SameSite=Strict`
  on every token-refresh response.
- In local development (HTTP, not HTTPS), the `Secure` flag must be relaxed;
  use an environment variable to toggle this.
- The access token lives in memory only — it is lost on page refresh. The
  client must silently re-fetch it using the cookie-held refresh token on load.
  This is standard behaviour and must be handled in the frontend auth flow.
