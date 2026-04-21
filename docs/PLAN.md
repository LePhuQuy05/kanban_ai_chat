# Project Delivery Plan

This plan is the execution checklist for the MVP in `AGENTS.md`.
Testing scope for this project is **unit + integration tests only**.
Coverage guidance: target around **80% when sensible**, prioritize high-value tests, and do not add low-value tests solely to hit a number.

## Part 1: Planning and Project Alignment

### Checklist
- [x] Expand `docs/PLAN.md` with actionable substeps, tests, and success criteria for all parts.
- [x] Create `frontend/AGENTS.md` documenting the current frontend code and constraints.
- [x] Confirm model slug for AI calls is exactly `openai/gpt-oss-120b/free`.
- [x] Confirm database direction: relational tables plus JSON metadata fields.
- [x] Request user approval on the plan before Part 2.

### Tests
- [x] No runtime tests required; verify documents are internally consistent and unambiguous.

### Success criteria
- [x] Plan is detailed enough to execute sequentially without guessing.
- [x] User explicitly confirms or requests edits before scaffolding starts.

## Part 2: Scaffolding (Docker + FastAPI hello world)

### Checklist
- [x] Create backend app scaffold in `backend/` using FastAPI.
- [x] Add containerization files to run backend + built frontend in one Docker image.
- [x] Configure Python dependency management with `uv` inside container build/runtime flow.
- [x] Add start/stop scripts in `scripts/` for Windows, macOS, and Linux.
- [x] Serve a simple static `hello world` HTML page at `/` from FastAPI first.
- [x] Add one demo API endpoint and verify page can call it successfully.
- [x] Document local run steps briefly.

### Tests
- [x] Unit: backend health and demo endpoint behavior.
- [x] Integration: container boot, `/` serves html, frontend script reaches backend endpoint.

### Success criteria
- [x] `docker` run brings up app locally with a visible hello page.
- [x] Demo API call round trip succeeds from served page.
- [x] Start/stop scripts work on target OS shells.

## Part 3: Add Existing Frontend Build and Serve at `/`

### Checklist
- [x] Wire Docker/backend serving so Next.js frontend is built and served from FastAPI at `/`.
- [x] Replace hello world page with the existing Kanban frontend output.
- [x] Keep route and static asset serving stable in container mode.
- [x] Preserve current Kanban interactions (rename, add/remove cards, drag/drop).

### Tests
- [x] Unit: existing frontend unit tests stay green.
- [x] Integration: app served through backend container renders Kanban at `/`.

### Success criteria
- [x] Visiting `/` in local container shows the current demo Kanban UI.
- [x] No regressions in existing board behavior.

## Part 4: Fake Sign-In Experience

### Checklist
- [x] Add login gate at `/` requiring credentials `user` / `password`.
- [x] Add logout action that returns user to the login view.
- [x] Keep auth flow simple and explicit for MVP (no over-engineering).
- [x] Ensure board is only visible when signed in.

### Tests
- [x] Unit: credential check and auth state helpers.
- [x] Integration: login success, login failure, logout, route gating behavior.

### Success criteria
- [x] Unauthenticated users cannot access Kanban UI.
- [x] Valid credentials unlock board; logout hides it again.

## Part 5: Database Modeling (Relational + JSON Metadata)

### Checklist
- [x] Design relational schema for users, board, columns, and cards.
- [x] Add JSON column(s) for flexible metadata (for cards and/or board-level metadata).
- [x] Define how MVP single-board-per-user is enforced.
- [x] Document schema and rationale in `docs/` with examples.
- [x] Request user sign-off before backend API implementation.

### Tests
- [x] Unit: schema creation helpers and serialization/deserialization of metadata JSON.
- [x] Integration: migration/init creates DB and tables correctly on empty environment.

### Success criteria
- [x] Schema supports current MVP and future multi-user extension.
- [x] JSON metadata usage is clearly scoped and documented.
- [ ] User confirms the design.

## Part 6: Backend Kanban API

### Checklist
- [x] Implement DB initialization if database file does not exist.
- [x] Add API routes to read board data for a user.
- [x] Add API routes to update board/columns/cards for a user.
- [x] Validate payloads and keep API shapes minimal.
- [x] Keep hardcoded MVP sign-in behavior compatible with user table model.

### Tests
- [x] Unit: service/repository logic for reads/writes and validation.
- [x] Integration: API + DB behavior for create/read/update paths and empty DB startup.

### Success criteria
- [x] Backend can persist and return Kanban state reliably per user.
- [x] DB auto-creation works without manual setup.

## Part 7: Frontend + Backend Persistence

### Checklist
- [ ] Replace frontend in-memory board state with backend-backed data fetch/update.
- [ ] Load board from API on login/session entry.
- [ ] Persist rename/add/remove/move card actions through backend APIs.
- [ ] Add loading/error states that keep UX clear but simple.

### Tests
- [ ] Unit: frontend data adapters/state update helpers.
- [ ] Integration: user actions mutate backend state and survive refresh.

### Success criteria
- [ ] Kanban edits are persistent across page reloads.
- [ ] UI remains responsive and consistent with stored backend state.

## Part 8: AI Connectivity via OpenRouter

### Checklist
- [ ] Implement backend AI client using OpenRouter with env key `OPENROUTER_API_KEY`.
- [ ] Use exact model slug `openai/gpt-oss-120b/free`.
- [ ] Add a simple backend route/service to run connectivity check prompt (`2+2`).
- [ ] Handle and log API errors cleanly.

### Tests
- [ ] Unit: request construction and response parsing.
- [ ] Integration: mocked OpenRouter test plus optional live connectivity smoke test.

### Success criteria
- [ ] Backend can successfully call OpenRouter and parse the response.
- [ ] Connectivity path is reliable enough for chat integration.

## Part 9: AI Structured Output for Chat + Optional Board Updates

### Checklist
- [ ] Define structured output schema: assistant reply + optional board mutation payload.
- [ ] Send board JSON snapshot, conversation history, and user message in each AI request.
- [ ] Validate AI response against schema before applying any mutation.
- [ ] Apply accepted board updates through the same persistence path as manual edits.
- [ ] Return both chat text and mutation result to frontend.

### Tests
- [ ] Unit: schema validation, transformation, and guardrails for malformed AI output.
- [ ] Integration: endpoint behavior with no-op response, valid mutation, and invalid payload.

### Success criteria
- [ ] AI responses are schema-safe and deterministic for the app contract.
- [ ] Optional board updates are applied only when valid.

## Part 10: Sidebar AI Chat UI + Auto Refresh

### Checklist
- [ ] Add right sidebar chat widget aligned with project color/theme rules.
- [ ] Support multi-turn conversation history in UI.
- [ ] Connect chat submission to backend AI endpoint.
- [ ] When AI returns board updates, refresh board state automatically in UI.
- [ ] Keep UX polished but MVP-simple.

### Tests
- [ ] Unit: chat state reducers/helpers and update handlers.
- [ ] Integration: send message, receive reply, apply AI-triggered board update, verify UI refresh.

### Success criteria
- [ ] User can chat naturally in sidebar and see responses.
- [ ] AI-driven board updates appear automatically without manual reload.

## Gate and Approval Flow

After each part, provide:
- What was implemented
- Test results (unit + integration)
- Any open risks or tradeoffs

Then ask: **"Here’s the detailed output for Part X. Please confirm or suggest changes before I continue."**
