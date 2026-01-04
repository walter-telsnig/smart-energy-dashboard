# Database Import Instructions

This document describes how to import the PV data for years 2025, 2026, and 2027 into the PostgreSQL database running in Docker.

## Prerequisites

-   Docker container `postgres-db` is running.
-   Database `pv-db` exists.
-   Tables `pv` (for hourly data) and `pv_minute` (for 15-minute data) exist.

## Import Process

### 1. Hourly Data (Table `pv`)

Run the following commands to import the hourly PV data:

```powershell
# 2025 Hourly Data
docker cp "infra/data/pv/pv_2025_hourly.csv" postgres-db:/tmp/pv_2025_hourly.csv
docker exec -i postgres-db psql -U postgres -d pv-db -c "\COPY pv(datetime, production_kw) FROM '/tmp/pv_2025_hourly.csv' DELIMITER ',' CSV HEADER;"
docker exec postgres-db rm /tmp/pv_2025_hourly.csv

# 2026 Hourly Data
docker cp "infra/data/pv/pv_2026_hourly.csv" postgres-db:/tmp/pv_2026_hourly.csv
docker exec -i postgres-db psql -U postgres -d pv-db -c "\COPY pv(datetime, production_kw) FROM '/tmp/pv_2026_hourly.csv' DELIMITER ',' CSV HEADER;"
docker exec postgres-db rm /tmp/pv_2026_hourly.csv

# 2027 Hourly Data
docker cp "infra/data/pv/pv_2027_hourly.csv" postgres-db:/tmp/pv_2027_hourly.csv
docker exec -i postgres-db psql -U postgres -d pv-db -c "\COPY pv(datetime, production_kw) FROM '/tmp/pv_2027_hourly.csv' DELIMITER ',' CSV HEADER;"
docker exec postgres-db rm /tmp/pv_2027_hourly.csv
```

### 2. 15-Minute Data (Table `pv_minute`)

Run the following commands to import the 15-minute resolution PV data:

```powershell
# 2025 15-min Data
docker cp "infra/data/pv/pv_2025_dach_15min.csv" postgres-db:/tmp/pv_2025_dach_15min.csv
docker exec -i postgres-db psql -U postgres -d pv-db -c "\COPY pv_minute(datetime, production_kw) FROM '/tmp/pv_2025_dach_15min.csv' DELIMITER ',' CSV HEADER;"
docker exec postgres-db rm /tmp/pv_2025_dach_15min.csv

# 2026 15-min Data
docker cp "infra/data/pv/pv_2026_dach_15min.csv" postgres-db:/tmp/pv_2026_dach_15min.csv
docker exec -i postgres-db psql -U postgres -d pv-db -c "\COPY pv_minute(datetime, production_kw) FROM '/tmp/pv_2026_dach_15min.csv' DELIMITER ',' CSV HEADER;"
docker exec postgres-db rm /tmp/pv_2026_dach_15min.csv

# 2027 15-min Data
docker cp "infra/data/pv/pv_2027_dach_15min.csv" postgres-db:/tmp/pv_2027_dach_15min.csv
docker exec -i postgres-db psql -U postgres -d pv-db -c "\COPY pv_minute(datetime, production_kw) FROM '/tmp/pv_2027_dach_15min.csv' DELIMITER ',' CSV HEADER;"
docker exec postgres-db rm /tmp/pv_2027_dach_15min.csv
```

## Verification

You can verify the data import by counting the rows in each table:

```powershell
# Check row count for pv table (should be 8760 * 3 = 26280)
docker exec -i postgres-db psql -U postgres -d pv-db -c "SELECT count(*) FROM pv;"

# Check row count for pv_minute table (should be 35040 * 3 = 105120 approx)
docker exec -i postgres-db psql -U postgres -d pv-db -c "SELECT count(*) FROM pv_minute;"
```
