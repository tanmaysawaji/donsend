# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- V1 requirements doc (`docs/requirements/v1.md`)
- ADR-0002: store JWT refresh token in an httpOnly cookie
- ADR-0003: authenticate WebSocket connections with a short-lived ticket
- Walking skeleton: FastAPI health endpoint, React frontend, Docker Compose,
  GitHub Actions CI
- Raspberry Pi 4B server setup: Ubuntu Server 24.04, Docker, Caddy (TLS),
  DuckDNS DDNS — app live at https://donsend.duckdns.org
- Dependabot for automated dependency updates (npm, pip, GitHub Actions)
- CodeQL scanning on every PR and weekly schedule
- Branch protection on main: PR required, CI must pass, force pushes blocked
- GPG commit signing
- V1 database schema: `users`, `invite_codes`, `friendships`, `messages`
  tables via SQLAlchemy models and an initial Alembic migration
- ADR-0004: V1 database schema — users, invite codes, friendships, messages
- Admin CLI script to generate single-use invite codes
  (`uv run python -m scripts.create_invite`)
- Password hashing utility using Argon2id (`app/core/security.py`)
- `sessions` table for single-active-session refresh token rotation
- ADR-0005: refresh token rotation via a single-session table
- Access token JWT create/decode utilities (`app/core/security.py`)
- `POST /auth/register` endpoint: validates a single-use invite code, checks
  email/username uniqueness, hashes the password, and creates the user
- `POST /auth/login` endpoint: verifies credentials in constant time, issues
  an access token, and sets a rotated refresh token as an httpOnly cookie
- `POST /auth/refresh` endpoint: rotates the refresh token and issues a new
  access token
- `POST /auth/logout` endpoint: deletes the session and clears the refresh
  token cookie, idempotently
