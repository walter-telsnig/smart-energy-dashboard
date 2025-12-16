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