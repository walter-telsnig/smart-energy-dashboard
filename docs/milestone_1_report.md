# 🧱 Milestone 1 – Technical Setup & Proof of Concept
**Course:** Advanced Software Engineering (623.503)  
**Project:** Smart Energy Dashboard  
**Team:** Yuliia Lomonosova, Patrick James Malapit, Sabrina Muhrer, Naga Pranusha Munjuluru, Walter Telsnig  
**Date:** 11 Dec 2025

---

## 1️⃣ Scope & Goal
Milestone 1 demonstrates a functioning technical stack and a minimal end-to-end workflow:
- Environment setup (Docker, venv, PostgreSQL placeholder)
- First working module (Account CRUD + PV Data)
- Build pipeline (automated tests + linting + CI)
- Architectural alignment with Clean Architecture principles (SRP, OCP, DIP, ADP, SDP, SAP)

---

## 2️⃣ Current Architecture
**Style:** Monolithic (“Monolith First”) with modular structure.

### 📂 Project Directory Structure
```
smart-energy-dashboard/
├── app/
│   └── api/
│       └── v1/
│           ├── accounts.py
│           ├── pv.py
│           └── main.py
├── core/
│   ├── config.py
│   ├── db.py
│   └── logging.py
├── infra/
│   ├── accounts/
│   ├── pv/
│   ├── data/
│   │   └── pv/
│   │       ├── pv_2025_hourly.csv
│   │       ├── pv_2026_hourly.csv
│   │       └── pv_2027_hourly.csv
│   └── migrations/
├── modules/
│   ├── accounts/
│   └── pv/
├── tests/
│   ├── test_accounts.py
│   └── test_pv.py
├── alembic.ini
├── README.md
└── docs/
    └── MILESTONE1_REPORT.md
```

| Layer | Purpose | Example |
|-------|----------|----------|
| `app/api/v1` | REST layer (FastAPI routers, OpenAPI docs) | `/api/v1/pv`, `/api/v1/accounts` |
| `modules/` | Business logic (modular domains) | `accounts`, `pv` |
| `infra/` | Data + persistence (SQLAlchemy, Alembic, CSV data) | `infra/data/pv/pv_2026_hourly.csv` |
| `core/` | Shared utilities (config, logging, db) | `core/db.py` |
| `tests/` | Unit tests (Pytest) | All pass ✅ (5 tests) |

**Design Principles applied:**  
- **SRP** – each module handles one responsibility  
- **OCP** – extendable via new routers without core modifications  
- **DIP** – database access via repository abstraction  
- **ADP/SDP/SAP** – dependencies flow in one direction (core → infra → api)

---

## 3️⃣ Implemented Features
- ✅ `Accounts` module: CRUD operations, unit tested  
- ✅ `PV` module: static CSV catalog, data preview (`/head`, `/catalog`)  
- ✅ Test suite (`pytest`), 100 % pass  
- ✅ Documentation (`README.md`)  
- ✅ CI workflows (`hello-python.yml`, `ci.yml`) running successfully  
- 🔧 Database integration (PostgreSQL) to be added in later milestones

---

## 4️⃣ Quality Gates (CI/CD)
| Gate | Tool | Status |
|------|------|--------|
| Unit Tests | pytest | ✅ local |
| Linting / Typing | ruff + mypy | ✅ local |
| Build Pipeline | GitHub Actions (`ci.yml`) | ✅ passing |
| Migrations | Alembic | ✅ manual verified |
| Docker Build | skipped (no Dockerfile yet) | ➖ deferred |

---

## 5️⃣ Proof of Concept Result
End-to-end data flow verified:  
**API → Service → Repository → CSV/DB → API response**  
All modules compile, run, and serve realistic PV data.

---

## 6️⃣ Planned Milestones Overview

### 🧱 Milestone 1 – Technical Setup & Proof of Concept (✅ Completed)
- FastAPI app running with modular monolith structure
- CI pipeline green (pytest, ruff, mypy)
- CRUD for Accounts and PV Data modules implemented
- Documentation and badges integrated

### 🔐 Milestone 2 – Authentication & Accounts Expansion
- Add JWT authentication (login/registration endpoints)
- Secure CRUD operations
- Extend Accounts model with hashed passwords and roles
- Introduce dependency injection for authentication guards
- Add unit tests for auth workflows

### 🐳 Milestone 3 – DevOps Slice: PostgreSQL & Docker Compose
- Integrate PostgreSQL as persistent DB layer
- Create Dockerfile + docker-compose.yml for local deployment
- Automate migrations (Alembic) inside containers
- Verify multi-service build pipeline in CI (FastAPI + DB)
- Seed demo data automatically on startup

### 📊 Milestone 4 – Analytics & Demo Readiness
- Implement Analytics module (KPIs, forecast accuracy, charts)
- Add visualization/dashboard frontend (e.g., Streamlit)
- Prepare live demo dataset and interactive endpoints
- Finalize ADR documentation and MkDocs site
- Deliver demo-ready release (v1.0)

### 🧩 Milestone 5 – Optional Enhancements (Stretch Goals)
- Add CI/CD deployment to cloud (Render, Fly.io, or GitHub Pages for docs)
- Extend metrics and monitoring (Prometheus/Grafana integration)
- Enable modular transition to microservices if time allows

---

## 7️⃣ References
- Macho, C. *Advanced Software Engineering – Lectures 1–2* (2025)  
- Martin, R.C. *Clean Architecture* (2018)  
- Kruchten, P. *4 + 1 View Model of Architecture* (1995)  
- Fowler, M. *Monolith First* (2015)

---

## ✅ Milestone 1 — Completion Checklist
- [x] FastAPI app runs (PoC) and serves endpoints.
- [x] **Accounts** CRUD available.
- [x] **PV** endpoints working: `/api/v1/pv`, `/api/v1/pv/head`, `/api/v1/pv/catalog` (CSV 2025–2027).
- [x] **CI green on `main`** (`.github/workflows/ci.yml`).
- [x] **Hello workflow** green (`hello-python.yml`).
- [x] **Tests pass** (`pytest`).
- [x] **Linting & typing pass** (Ruff, MyPy).
- [x] **Badges** added in `README.md` (CI + Hello).
- [x] **Documentation**: this `MILESTONE1_REPORT.md` in `docs/`.
- [ ] **Database** (PostgreSQL via Docker Compose) — *Deferred to Milestone 3.*
  - _Note:_ A dedicated Postgres instance is **not required for Milestone 1**; PoC may use in-memory/SQLite or mock data. We will introduce Postgres + Compose in Milestone 3.
- [ ] **Seed data** script (defer with Postgres).
- [ ] **ADR-001 Monolith First** (optional but recommended for traceability).

### 🎬 Demo script (2–3 min)
1. Open GitHub **Actions** → show last green run for **Smart Energy Dashboard CI**.
2. Open `README.md` → point to green **badges**.
3. Start API locally → show `/docs` (Swagger) and call PV endpoints.
4. Close with the note: *Database containerization is planned for Milestone 3; current PoC uses CSV-backed data and passes CI quality gates.*

**Milestone 1 status:** ✅ **Completed**

