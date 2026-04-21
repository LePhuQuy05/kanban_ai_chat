# Backend Notes

Current backend through Part 5 includes:

- Entry point: `backend/app/main.py`
- Root route: serves exported frontend static files when available.
- Demo API route: `GET /api/hello` returns JSON payload.
- Kanban API routes:
  - `GET /api/board`
  - `PUT /api/board`
  - both use the demo auth headers `X-Username` / `X-Password`
- If static frontend build is missing, root returns a fallback HTML message.
- Legacy hello world HTML helper remains in `backend/app/views.py` from Part 2 scaffold.
- Database schema/init helpers live in `backend/app/db.py`.
- Board persistence and seeding logic live in `backend/app/board_service.py`.
- API payload validation models live in `backend/app/schemas.py`.
- Schema documentation lives in `docs/DB_SCHEMA.md`.
- Tests live in `backend/tests/`:
  - `test_views.py` (unit-style content checks)
  - `test_app_integration.py` (route-level integration checks with TestClient)
  - `test_db.py` (schema creation, JSON metadata, and single-board constraint checks)
  - `test_board_service.py` (board seeding, persistence, and validation checks)
  - `test_board_api.py` (API auth, read/update, and payload validation checks)

The backend now persists board state for the demo user. Part 7 will connect the frontend to these routes and remove the temporary browser-only persistence path.
