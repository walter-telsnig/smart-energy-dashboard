# ADR-002: Add a read-only Streamlit demo UI for Milestone 1

- **Status:** Accepted (2025-10-XX)
- **Deciders:** Team Smart Energy Dashboard
- **Context:** We need a minimal, user-visible demo for Milestone 1 that showcases end-to-end data flow (PV CSV → API → chart) without increasing coupling or delivery risk. The backend is a modular monolith (FastAPI + SQLAlchemy), and we want to keep the presentation layer optional and replaceable.

## Decision

We introduce a small **read-only Streamlit UI** (`/ui/app.py`) that **only consumes** the FastAPI REST API.  
Key constraints:

- The UI **does not** import backend modules or touch the database directly.
- The API enforces a stable response shape for time series (`timestamp`, `value`).
- The UI is started independently (local or via `docker compose`) and may be removed/swapped later without backend changes.

## Rationale

- **Fast feedback** for stakeholders while keeping **architecture boundaries** clear (SRP, ADP).
- **Low cost** to implement and demo, compared to a full SPA.
- Keeps future options open (replace with React, Grafana, or no UI at all).

## Consequences

**Positive**
- Quick end-to-end demo validating the vertical slice (dev-experience, data paths, contracts).
- Clean seam between UI and API; easier future migration.

**Negative**
- Streamlit is not our final UI; styling and routing are limited.
- Two processes during dev (API + UI) and duplicate dependency install unless we optimize Dockerfiles.

## Options Considered

- **Streamlit (chosen):** very fast to prototype, Python-native.
- **No UI yet:** simpler, but fails the “visible functionality” expectation for M1.
- **React/Vite frontend:** powerful and closer to a product UI, but higher effort and risk for M1.

## Implementation Notes

- Folder: `ui/app.py` (no imports from backend packages).
- Env: `API_BASE` default `http://localhost:8000/api/v1`.
- Docker Compose: two services `api` and `ui` for local dev.
- Back-end endpoint contract: `/api/v1/pv/catalog`, `/api/v1/pv/head?key=&n=` return normalized JSON.

## Migration (Milestone 2+)

- Add tests (unit/integration) around the PV endpoints and UI HTTP client.
- Introduce quality gates (coverage, ruff, mypy) in CI.
- Optionally replace Streamlit with a more robust UI or keep it as a diagnostics console.
