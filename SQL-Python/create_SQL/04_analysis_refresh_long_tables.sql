-- Reconstruct the missing long-table refresh logic from the staging schemas.
-- One row per location and observed period. Prices remain nominal CAD amounts.
-- House: CREA seasonally adjusted monthly composite benchmark prices.
-- Rent: CMHC Row / Apartment October survey, Total monthly rent in CAD.
-- Preserve numeric NULLs. No interpolation, forward fill, or CPI adjustment here.

CREATE SCHEMA IF NOT EXISTS analysis;

CREATE TABLE IF NOT EXISTS analysis.city_house_prices_long (
    date_period DATE,
    city TEXT,
    price NUMERIC
);

DELETE FROM analysis.city_house_prices_long;

INSERT INTO analysis.city_house_prices_long (date_period, city, price)
SELECT house.date_period, city_data.city, city_data.price
FROM stg.city_house_prices AS house
CROSS JOIN LATERAL (
    VALUES
        ('Canada', house.canada_price),
        ('Vancouver', house.vancouver_price),
        ('Calgary', house.calgary_price),
        ('Edmonton', house.edmonton_price),
        ('Toronto', house.toronto_price),
        ('Ottawa', house.ottawa_price),
        ('Montreal', house.montreal_price)
) AS city_data(city, price)
WHERE house.date_period IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_analysis_house_long_city_date
ON analysis.city_house_prices_long (city, date_period);

CREATE TABLE IF NOT EXISTS analysis.city_rent_long (
    date_period DATE,
    city TEXT,
    price NUMERIC
);

DELETE FROM analysis.city_rent_long;

INSERT INTO analysis.city_rent_long (date_period, city, price)
SELECT rent.date_period, city_data.city, city_data.price
FROM stg.city_rent AS rent
CROSS JOIN LATERAL (
    VALUES
        ('Canada', rent.canada_price),
        ('Vancouver', rent.vancouver_price),
        ('Calgary', rent.calgary_price),
        ('Edmonton', rent.edmonton_price),
        ('Toronto', rent.toronto_price),
        ('Ottawa', rent.ottawa_price),
        ('Montreal', rent.montreal_price)
) AS city_data(city, price)
WHERE rent.date_period IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_analysis_rent_long_city_date
ON analysis.city_rent_long (city, date_period);
