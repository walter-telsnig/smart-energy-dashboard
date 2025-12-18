create table consumption (
	datetime TIMESTAMP Not Null Primary Key,
	consumption_kwh Float
);

create table market (
	datetime TIMESTAMP Not Null Primary Key,
	price_eur_mwh Float
);

create table pv (
	datetime TIMESTAMP Not Null Primary Key,
	production_kw Float
);

create table weather (
	datetime TIMESTAMP Not Null Primary Key,
	temp_c Float,
	cloud_cover_pct Float
);