# Inventory Management System

A production inventory system built for real daily use — kitchen staff record stock in seconds, managers oversee purchasing and corrections, and leadership gets an at-a-glance view of what's healthy, low, or needs attention.

**Guiding principle:** simple to use, not simplistic. The interface stays fast and visual for kitchen use; the backend underneath stays fully auditable, transactional, and role-secured.

---

## What it does

- **Kitchen staff** tap an item's photo, tap Used or Received, tap a quantity — done in a few taps, no typing required.
- **Managers** edit items, correct mistakes via adjustments (never by silently rewriting history), manage the purchase list, and review activity.
- **Admins** manage users, locations, categories, and resolve data that still needs confirmation.
- Every stock change is a permanent, timestamped movement record — nothing is ever overwritten, only corrected.
- Low stock is detected automatically by deterministic threshold rules (not AI) and feeds a purchase-list workflow.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + TypeScript + Tailwind CSS |
| Backend | FastAPI (Python) |
| Database & Auth | Supabase (PostgreSQL, Auth, Storage) |
| Backend hosting | Render |
| Frontend hosting | Vercel |
| CI | GitHub Actions |

---

## Architecture, in one picture

```
┌─────────────────────┐
│  React frontend       │  Role-aware UI: kitchen / manager / admin
└──────────┬────────────┘
           │ HTTPS, bearer token (Supabase-issued)
           ▼
┌─────────────────────┐
│      FastAPI           │  ← single authorization boundary
│  - JWT verification    │
│  - Role enforcement    │
│  - Transactional stock │
│    movement engine     │
│  - Audit logging       │
└──────────┬────────────┘
           │
           ▼
┌─────────────────────┐      ┌─────────────────────┐
│  Supabase Postgres     │◄────►│  Supabase Storage    │
│  - Row Level Security  │      │  (product photos)     │
│  - Immutable movement/ │      └─────────────────────┘
│    audit history        │
└─────────────────────┘
```

Every stock change (Receive / Use / Adjust / Transfer) runs inside one atomic database transaction, is protected against duplicate submissions (idempotency keys), and is safe under concurrent use (row-level locking) — two people recording stock on the same item at the same instant can never silently overwrite each other.

---

## CI/CD pipeline

```
 Push to GitHub (main)
        │
        ▼
 GitHub Actions
   ├── Backend:  pytest  (RBAC, concurrency, idempotency, IDOR checks)
   └── Frontend: npm run build
        │
        │   only if BOTH succeed
        ▼
 ┌───────────────┐      ┌───────────────┐
 │ Render          │      │ Vercel          │
 │ (backend deploy)│      │ (frontend deploy)│
 └───────────────┘      └───────────────┘
        │                        │
        ▼                        ▼
   Live backend API        Live web app
```

A failing test or a broken build stops the pipeline before either platform deploys — the previous, working version stays live. Nothing reaches production without passing automated checks first.

---

## Project structure

```
inventory-system/
├── backend/            FastAPI app, routers, business logic, tests
├── frontend/            React app (pages, components, auth)
├── supabase/
│   └── migrations/     Ordered SQL migrations (schema, RLS, seed data)
└── .github/workflows/  CI: backend tests, frontend build + deploy
```

---

## Status

Core system complete: authentication & roles, inventory catalog, monthly stock periods, the full stock-movement engine, purchase-list automation, secure image uploads, admin management screens, and a gated CI/CD pipeline.

Email/scheduled alerts are designed for but intentionally not yet enabled.