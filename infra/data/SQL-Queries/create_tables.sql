create table consumption (
	datetime TIMESTAMP Not Null Primary Key,
	consumption_kwh Float
);

create table consumption_minute (
	datetime TIMESTAMP Not Null Primary Key,
	consumption_kwh Float,
	household_general_kwh Float,
	heat_pump_kwh Float,
	ev_load_kwh Float,
	household_base_kwh Float,
	total_consumption_kwh Float,
	battery_soc_kwh Float,
	battery_charging_kwh Float,
	battery_discharging_kwh Float,
	grid_export_kwh Float,
	grid_import_kwh Float
);

create table market (
	datetime TIMESTAMP Not Null Primary Key,
	price_eur_mwh Float
);

create table market_minute (
	datetime TIMESTAMP Not Null Primary Key,
	price_eur_mwh Float
);

create table pv (
	datetime TIMESTAMP Not Null Primary Key,
	production_kw Float
);

create table pv_minute (
	datetime TIMESTAMP Not Null Primary Key,
	production_kw Float
);

create table weather (
	datetime TIMESTAMP Not Null Primary Key,
	temp_c Float,
	cloud_cover_pct Float
);