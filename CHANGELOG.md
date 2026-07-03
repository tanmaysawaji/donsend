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
