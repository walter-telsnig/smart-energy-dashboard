# Database Import Instructions

This document describes how to import the data for years 2025, 2026, and 2027 into the PostgreSQL database running in Docker.

## Automated Import Script

The easiest way to import all data (PV, Consumption, Weather, Market) is to use the provided PowerShell script.

### Prerequisites

-   Docker container `postgres-db` is running.
-   Database `pv-db` exists and has the required tables.

### Run the Script

Run the following command from the root of the repository:

```powershell
./infra/data/import_all_data.ps1
```

This script will:
1.  Import hourly and 15-minute data for **PV**, **Consumption**, and **Market**.
2.  Import hourly data for **Weather**.
3.  Handle years 2025, 2026, and 2027.
4.  Automatically clean up temporary files in the container.

## Verification

You can verify the data import by checking the row counts in the database tables:

```powershell
# Check row count for hourly tables (should be ~26280 each)
docker exec -i postgres-db psql -U postgres -d pv-db -c "SELECT count(*) FROM pv;"
docker exec -i postgres-db psql -U postgres -d pv-db -c "SELECT count(*) FROM consumption;"
docker exec -i postgres-db psql -U postgres -d pv-db -c "SELECT count(*) FROM weather;"
docker exec -i postgres-db psql -U postgres -d pv-db -c "SELECT count(*) FROM market;"

# Check row count for 15-minute tables (should be ~105120 each)
docker exec -i postgres-db psql -U postgres -d pv-db -c "SELECT count(*) FROM pv_minute;"
docker exec -i postgres-db psql -U postgres -d pv-db -c "SELECT count(*) FROM consumption_minute;"
docker exec -i postgres-db psql -U postgres -d pv-db -c "SELECT count(*) FROM market_minute;"
```


old script docker
services:
  db:
    image: postgres:15
    container_name: postgres-db
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: pv-db
    volumes:
      - ./data:/var/lib/postgres/data