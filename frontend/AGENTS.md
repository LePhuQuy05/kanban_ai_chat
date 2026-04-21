# Frontend Codebase Notes

This document describes the current frontend implementation in `frontend/` so backend/container integration can preserve behavior.

## Stack

- Next.js (App Router) + React + TypeScript
- Tailwind CSS v4
- Drag-and-drop via `@dnd-kit`
- Unit tests with Vitest + Testing Library
- Browser integration tests with Playwright (existing, optional for MVP test gate)

## Entrypoints and structure

- `src/app/page.tsx` renders `KanbanBoard`.
- `src/components/KanbanBoard.tsx` owns board state and drag/drop orchestration.
- `src/components/KanbanColumn.tsx` renders per-column UI, rename input, card list, add-card form.
- `src/components/KanbanCard.tsx` renders sortable card and delete action.
- `src/components/NewCardForm.tsx` handles add-card form toggle and submission.
- `src/lib/kanban.ts` contains domain types, seed board data, ID generation, and `moveCard` logic.

## Current behavior

- Five fixed columns are present by default.
- Column names are editable inline.
- Cards can be:
  - Reordered within a column
  - Moved across columns
  - Added to a column
  - Removed from a column
- Board state is currently in-memory (React state); no backend persistence yet.

## Testing today

- Unit tests exist for:
  - Drag/drop movement logic in `src/lib/kanban.test.ts`
  - Core board interactions in `src/components/KanbanBoard.test.tsx`
- Integration/e2e coverage exists with Playwright in `tests/kanban.spec.ts`.

## Constraints for upcoming work

- Preserve existing board interactions while integrating backend persistence.
- Keep implementation simple and avoid over-engineering.
- Follow project palette defined in root `AGENTS.md`.
- For MVP delivery gates, prioritize unit + integration verification.
