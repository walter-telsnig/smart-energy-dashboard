# ADR-003: Extension of Time-Series Data and API Access Strategy

## Context
The Smart Energy Dashboard project initially provided only **PV (photovoltaic)** time-series data for 2025–2027 in hourly resolution.  
The system required additional data for:
- **Market electricity prices** (€/MWh, EPEX Spot AT zone)  
- **Household electricity consumption** (kWh, 4 500 kWh per year)

At the same time, the team discussed whether these new datasets should also be served through **FastAPI endpoints**, similar to the existing `/api/v1/pv` service.

---

## Decision
1. **Added new data sets**
   - **Market data** (`infra/data/market/price_YYYY_hourly.csv`):  
     Hourly synthetic price curves (EPEX Spot AT) for 2025–2027, realistic seasonal and daily dynamics.
   - **Household consumption** (`infra/data/consumption/consumption_YYYY_hourly.csv`):  
     Hourly load profiles for 2025–2027, annual total ≈ 4 500 kWh, morning/evening peaks, weekend uplift.

2. **Resolution**
   - All new data remain **hourly**, matching the PV time series.  
     A later ADR will define the 15-minute migration when all data sources can change together (Conway’s & Common Closure Principles).

3. **API design choice**
   - **PV data** keep their dynamic FastAPI endpoints:
     - `/api/v1/pv/catalog`
     - `/api/v1/pv/head?key=…&n=…`
   - **Market** and **Consumption** data remain **static CSVs** for now.
   - Only PV requires live API access because:
     - PV generation is the main dynamic variable for simulation.
     - Endpoints already existed and are reused by the battery simulation pipeline.
     - Market & consumption data are static, local, and used only for visualization.

4. **Battery module**
   - Implemented full module (`modules/battery`) with greedy charge/discharge logic.
   - Added new API endpoints:
     - `POST /api/v1/battery/simulate`
     - `POST /api/v1/battery/cost-summary` (server-side cost aggregation)
   - Extended Streamlit UI (Battery Sim page) to call both endpoints and visualize SoC, flows, and cost KPIs.

5. **UI architecture**
   - Introduced multipage Streamlit structure (`ui/pages/`):
     - `01_PV.py` – PV from CSV or FastAPI  
     - `02_Prices.py` – Market prices (CSV)  
     - `03_Consumption.py` – Household load (CSV)  
     - `04_Compare.py` – Overlay PV/Price/Consumption + KPIs  
     - `99_Battery_Sim.py` – Simulation UI (server-connected)  
     - `00_Health.py` – new health-check page for CSV and API diagnostics

---

## Rationale
- **Simplicity (YAGNI):** Market & Consumption endpoints aren’t needed until remote deployment or multi-client access.  
- **Separation of concerns:** Battery simulation needs API access, but static visualization doesn’t.  
- **Maintainability:** Postpone additional endpoints until they deliver architectural value (e.g., unified 15-min data, security).  
- **Consistency:** Keep uniform file schema across all time-series (`datetime`, `value_column`).  
- **Monolith-first:** Continue developing within the modular monolith (FastAPI + Streamlit), deferring microservice breakout.

---

## Consequences
- ✅ Simpler local development (Streamlit reads CSVs directly).  
- ✅ PV/Battery APIs fully tested end-to-end.  
- 🔜 Future ADR: “Introduce Market & Consumption Endpoints for Multi-Client Access” once the dashboard is deployed or resolution changes to 15 min.
