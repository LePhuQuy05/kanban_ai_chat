# Kanban AI Chat

Kanban AI Chat is a local-first MVP project management web app that combines a Kanban board with an AI chat assistant. Users sign in, manage cards with drag-and-drop, and use sidebar chat to create, edit, and move cards through structured AI-driven updates.

## Features

- Simple MVP authentication with demo credentials (`user` / `password`)
- One board per user (schema supports future multi-user expansion)
- Kanban workflows: rename columns, add/remove cards, drag-and-drop reordering and movement
- Persistent board state backed by SQLite
- Sidebar AI chat powered by OpenRouter (`openai/gpt-oss-120b/free`)
- AI responses can optionally include validated board mutations applied through the same persistence path as manual edits

## Tech Stack

- Frontend: Next.js (App Router), React, TypeScript, Tailwind CSS, `@dnd-kit`
- Backend: FastAPI (Python), Pydantic
- Database: SQLite with relational tables plus JSON metadata fields
- Packaging/runtime: Docker + Docker Compose
- Python dependency management: `uv`

## Architecture

- `frontend/`: UI and client-side interaction logic
- `backend/`: API, board service, database initialization/schema, AI connectivity
- `scripts/`: start/stop scripts for Windows (`.bat`, `.ps1`) and macOS/Linux (`.sh`)
- `docs/`: delivery plan, schema notes, and run guidance

The backend serves the built frontend at `/` and provides API endpoints for auth-gated board reads/updates and AI chat operations.

## Local Run

### Prerequisites

- Docker Desktop (or Docker Engine + Compose)
- OpenRouter API key

### Environment

Create a `.env` file at repository root:

```env
OPENROUTER_API_KEY=your_key_here
```

### Start

- Windows PowerShell: `./scripts/start.ps1`
- Windows CMD: `scripts\start.bat`
- macOS/Linux: `./scripts/start.sh`

Then open [http://localhost:8000](http://localhost:8000).

### Stop

- Windows PowerShell: `./scripts/stop.ps1`
- Windows CMD: `scripts\stop.bat`
- macOS/Linux: `./scripts/stop.sh`

## API Overview

- `GET /api/board`: fetch authenticated user's board
- `PUT /api/board`: persist authenticated user's board updates
- AI chat endpoint: accepts conversation + board snapshot, returns assistant reply plus optional validated board update payload

MVP auth uses request headers:

- `X-Username`
- `X-Password`

## Testing

The project prioritizes unit and integration tests for MVP delivery:

- Backend tests in `backend/tests/`
- Frontend unit/integration tests in `frontend/src/**/*.test.ts(x)` and related test suites

Run tests from each app directory using the configured package/tool commands.

## MVP Scope

- Local Docker-based runtime
- Minimal, explicit auth flow
- Simple implementation choices over over-engineering
- Clear extension path for stronger auth and full multi-user capabilities in future iterations
