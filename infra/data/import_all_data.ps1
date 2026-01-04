# Import All Data Script
# This script imports PV, Consumption, Weather, and Market data for years 2025-2027
# into the Dockerized PostgreSQL database.

$years = @("2025", "2026", "2027")
$container = "postgres-db"
$db = "pv-db"
$user = "postgres"

Write-Host "Starting data import..."

# Clear existing data to avoid duplicates
Write-Host "Clearing existing data..."
docker exec -i $container psql -U $user -d $db -c "TRUNCATE TABLE pv, pv_minute, consumption, consumption_minute, weather, market, market_minute;"

foreach ($year in $years) {
    Write-Host "Processing year $year..."

    # --- PV Data ---
    # Hourly
    $pvHourly = "infra/data/pv/pv_${year}_hourly.csv"
    if (Test-Path $pvHourly) {
        Write-Host "  Importing PV Hourly ($year)..."
        docker cp $pvHourly "${container}:/tmp/pv.csv"
        docker exec -i $container psql -U $user -d $db -c "\COPY pv(datetime, production_kw) FROM '/tmp/pv.csv' DELIMITER ',' CSV HEADER;"
        docker exec $container rm /tmp/pv.csv
    } else {
        Write-Host "  Warning: $pvHourly not found."
    }

    # 15-Minute
    $pv15min = "infra/data/pv/pv_${year}_dach_15min.csv"
    if (Test-Path $pv15min) {
        Write-Host "  Importing PV 15-min ($year)..."
        docker cp $pv15min "${container}:/tmp/pv_minute.csv"
        docker exec -i $container psql -U $user -d $db -c "\COPY pv_minute(datetime, production_kw) FROM '/tmp/pv_minute.csv' DELIMITER ',' CSV HEADER;"
        docker exec $container rm /tmp/pv_minute.csv
    } else {
        Write-Host "  Warning: $pv15min not found."
    }

    # --- Consumption Data ---
    # Hourly
    $consHourly = "infra/data/consumption/consumption_${year}_hourly.csv"
    if (Test-Path $consHourly) {
        Write-Host "  Importing Consumption Hourly ($year)..."
        docker cp $consHourly "${container}:/tmp/consumption.csv"
        docker exec -i $container psql -U $user -d $db -c "\COPY consumption(datetime, consumption_kwh) FROM '/tmp/consumption.csv' DELIMITER ',' CSV HEADER;"
        docker exec $container rm /tmp/consumption.csv
    } else {
        Write-Host "  Warning: $consHourly not found."
    }

    # 15-Minute
    $cons15min = "infra/data/consumption/consumption_${year}_dach_15min.csv"
    if (Test-Path $cons15min) {
        Write-Host "  Importing Consumption 15-min ($year)..."
        docker cp $cons15min "${container}:/tmp/consumption_minute.csv"
        # Import all columns for consumption_minute as the CSV layout matches the table
        docker exec -i $container psql -U $user -d $db -c "\COPY consumption_minute FROM '/tmp/consumption_minute.csv' DELIMITER ',' CSV HEADER;"
        docker exec $container rm /tmp/consumption_minute.csv
    } else {
        Write-Host "  Warning: $cons15min not found."
    }

    # --- Weather Data ---
    # Hourly
    $weatherHourly = "infra/data/weather/weather_${year}_hourly.csv"
    if (Test-Path $weatherHourly) {
        Write-Host "  Importing Weather Hourly ($year)..."
        docker cp $weatherHourly "${container}:/tmp/weather.csv"
        docker exec -i $container psql -U $user -d $db -c "\COPY weather(datetime, temp_c, cloud_cover_pct) FROM '/tmp/weather.csv' DELIMITER ',' CSV HEADER;"
        docker exec $container rm /tmp/weather.csv
    } else {
        Write-Host "  Warning: $weatherHourly not found."
    }

    # --- Market Data ---
    # Hourly
    $marketHourly = "infra/data/market/price_${year}_hourly.csv"
    if (Test-Path $marketHourly) {
        Write-Host "  Importing Market Hourly ($year)..."
        docker cp $marketHourly "${container}:/tmp/market.csv"
        docker exec -i $container psql -U $user -d $db -c "\COPY market(datetime, price_eur_mwh) FROM '/tmp/market.csv' DELIMITER ',' CSV HEADER;"
        docker exec $container rm /tmp/market.csv
    } else {
        Write-Host "  Warning: $marketHourly not found."
    }

    # 15-Minute
    $market15min = "infra/data/market/price_${year}_dach_15min.csv"
    if (Test-Path $market15min) {
        Write-Host "  Importing Market 15-min ($year)..."
        docker cp $market15min "${container}:/tmp/market_minute.csv"
        docker exec -i $container psql -U $user -d $db -c "\COPY market_minute(datetime, price_eur_mwh) FROM '/tmp/market_minute.csv' DELIMITER ',' CSV HEADER;"
        docker exec $container rm /tmp/market_minute.csv
    } else {
        Write-Host "  Warning: $market15min not found."
    }
}

Write-Host "Data import completed."
