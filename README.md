![Smart Energy Dashboard](docs/images/ASE_Readme_Banner.png)


[![Smart Energy Dashboard CI](https://github.com/walter-telsnig/smart-energy-dashboard/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/walter-telsnig/smart-energy-dashboard/actions/workflows/ci.yml?query=branch%3Amain)
[![Hello Python](https://github.com/walter-telsnig/smart-energy-dashboard/actions/workflows/hello-python.yml/badge.svg)](https://github.com/walter-telsnig/smart-energy-dashboard/actions/workflows/hello-python.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=walter-telsnig_smart-energy-dashboard&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=walter-telsnig_smart-energy-dashboard)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=walter-telsnig_smart-energy-dashboard&metric=bugs)](https://sonarcloud.io/summary/new_code?id=walter-telsnig_smart-energy-dashboard)
![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-teal?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.50%2B-blue?logo=streamlit)
![Docker](https://img.shields.io/badge/Docker-24.0%2B-blue?logo=docker)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-blue?logo=postgresql)

## ⚡ About the Project

The Smart Energy Dashboard is a modular monolithic web application for visualizing and analyzing residential energy flows (PV production, consumption, storage). This project adheres to **layered architecture** and component principles (ADP, SDP, SAP) to ensure maintainability, scalability, and testability.
It is designed as an academic prototype emphasizing clean architecture, testability, and reproducibility rather than production-scale operation.
This project was developed as part of the course Advanced Software Engineering (WS 2025/26) at Alpen-Adria-Universität Klagenfurt.

---

## 🏛️ Tech Stack

- **Language:** Python 3.13
- **Backend:** FastAPI, SQLAlchemy, Alembic
- **Frontend:** Streamlit
- **Infrastructure:** Docker, Docker Compose
- **Database:** SQLite (Dev), PostgreSQL (Prod)

---

## ⚙️ Architecture

The system is organized into four distinct layers, with dependencies flowing strictly inward (Presentation → Application → Domain → Infrastructure).

| Layer | Description | Key Modules |
|-------|-------------|-------------|
| **Presentation** | Handles user interactions and API endpoints. | `app/`, `ui/` |
| **Application** | Orchestrates use cases and domain logic. | `modules/*/application/` |
| **Domain** | Contains core business entities and logic. | `modules/*/domain/` |
| **Infrastructure** | Manages persistence, external APIs, and system integration. | `infra/`, `modules/*/infrastructure/` |

### Key Design Principles
- **SRP (Single Responsibility Principle):** Strict separation of concerns (e.g., UI vs. Business Logic).
- **DIP (Dependency Inversion Principle):** High-level modules depend on abstractions (ports), not concrete implementations.
- **ADP (Acyclic Dependencies Principle):** No circular dependencies between modules.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.13+**
- **Git**
- **Docker Desktop** (optional, for milestones 3+)


### Installation

1.  **Clone the Repository**
    ```powershell
    git clone https://github.com/walter-telsnig/smart-energy-dashboard.git
    cd smart-energy-dashboard
    ```

2.  **Set up Virtual Environment**
    ```powershell
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    ```

3.  **Install Dependencies**
    ```powershell
    pip install -U pip
    pip install -r requirements.txt
    ```

4.  **Configure Environment**
    Create a `.env` file based on `.env.example`:
    ```ini
    SED_DB_URL=postgresql://<user>:<password>@localhost:5432/<database>
    API_BASE=http://localhost:8000/api/v1
    ```

### Running the Application

🐳 **Docker Compose**
Starts the API and Database containers.
```powershell
docker compose up -d
```

***Database Management in Docker:***
- Connect via `psql`: `docker exec -it postgres-db psql -U postgres -d pv-db`
- Connect via **pgAdmin**:
    - **Host:** `localhost`
    - **Port:** `5432`
    - **User/Password:** (See `docker-compose.yml`)

**FastAPI Backend**
 Starts the API server with hot-reload enabled.
```powershell
python -m uvicorn app.main:create_app --factory --reload --port 8000
```
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
- **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

**Streamlit Frontend**
Starts the interactive dashboard.
```powershell
streamlit run ui/app.py
```
**Dashboard:** [http://localhost:8501](http://localhost:8501)

### 🔐 Authentication & Users

The application uses **JWT Authentication**. You must log in to access the dashboard.

**Default Login:**
There are no default users. You must create a user account.





### Running Tests
Execute the test suite using Pytest.
```powershell
pytest -q
```

---

## Quality Assurance and Testing
All quality gates must pass before merging to `main`.

- Ruff: linting and formatting
- Mypy: static typing
- Pytest: unit and integration tests
- GitHub Actions: CI on push and PR
- Quality Gate: SonarQube [sonarcloud.io](https://sonarcloud.io/project/overview?id=walter-telsnig_smart-energy-dashboard)

## 🗺️ Project Scope & Roadmap

The project development is divided into strategic milestones:

- [x] **Milestone 1: API Layer & Accounts** - Basic CRUD and layered architecture setup.
- [x] **Milestone 2: Quality Gates** - CI pipeline, linting (Ruff), and type checking (Mypy).
- [x] **Milestone 3: DevOps Slice** - Dockerization and Postgres integration.
- [x] **Milestone 4: Authentication** - JWT implementation and secure access.
- [x] **Milestone 5: Visualization** - Advanced analytic dashboard with Streamlit, rule-based optimization.

Out of Scope:
- Real-time optimization (CPLEX, Gurobi, etc.)
- Live market data ingestion and Message Broker feature (e.g., Kafka, RabbitMQ)
