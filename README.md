# donsend

A simple, self-hosted chat service. Users register via invite, pick a unique
username, add each other as friends, and exchange real-time text messages.

Built as a learning project to practice the full software development lifecycle:
React + TypeScript frontend, FastAPI backend, PostgreSQL, Docker, and CI/CD.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript (Vite) |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Real-time | WebSockets |
| Auth | JWT — httpOnly cookie refresh token |
| Reverse proxy | nginx (TLS termination) |
| CI/CD | GitHub Actions |
| Containers | Docker + Docker Compose |

## Setup (local dev)

Prerequisites: Docker Desktop, Node.js (LTS), Python 3.12+, uv.

```bash
# Copy env file and fill in values
cp .env.example .env

# Start everything
docker compose up
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

## Development (without Docker)

```bash
# Backend
cd backend
uv sync
uv run fastapi dev

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Docs

- [`docs/requirements/v1.md`](docs/requirements/v1.md) — V1 scope and acceptance criteria
- [`docs/adr/`](docs/adr/) — architecture decision records
