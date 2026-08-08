-- Active: 1783423074019@@127.0.0.1@5432@rentvsbuy
CREATE SCHEMA IF NOT EXISTS raw;

DROP TABLE IF EXISTS raw.canada_house_price_index_2010_100;
CREATE TABLE raw.canada_house_price_index_2010_100 (
    dataflow_id      text,
    series_key       text,
    freq             text,
    ref_area         text,
    value_type       text,
    unit_measure     text,
    unit_name        text,
    unit_multiplier  text,
    time_period      text,
    obs_conf         text,
    obs_pre_break    text,
    obs_status       text,
    obs_value        numeric
);

DROP TABLE IF EXISTS raw.city_house_price_index;
CREATE TABLE raw.city_house_price_index (
    transaction_date text,
    
    c11_index text,
    c11_sa_index text,
    c11_smoothed_index text,
    c11_smoothed_sa_index text,
    c11_sales_pair_count text,

    bc_victoria_index text,
    bc_victoria_sa_index text,
    bc_victoria_smoothed_index text,
    bc_victoria_smoothed_sa_index text,
    bc_victoria_sales_pair_count text,

    bc_vancouver_index text,
    bc_vancouver_sa_index text,
    bc_vancouver_smoothed_index text,
    bc_vancouver_smoothed_sa_index text,
    bc_vancouver_sales_pair_count text,

    ab_calgary_index text,
    ab_calgary_sa_index text,
    ab_calgary_smoothed_index text,
    ab_calgary_smoothed_sa_index text,
    ab_calgary_sales_pair_count text,

    ab_edmonton_index text,
    ab_edmonton_sa_index text,
    ab_edmonton_smoothed_index text,
    ab_edmonton_smoothed_sa_index text,
    ab_edmonton_sales_pair_count text,

    mb_winnipeg_index text,
    mb_winnipeg_sa_index text,
    mb_winnipeg_smoothed_index text,
    mb_winnipeg_smoothed_sa_index text,
    mb_winnipeg_sales_pair_count text,

    on_hamilton_index text,
    on_hamilton_sa_index text,
    on_hamilton_smoothed_index text,
    on_hamilton_smoothed_sa_index text,
    on_hamilton_sales_pair_count text,

    on_toronto_index text,
    on_toronto_sa_index text,
    on_toronto_smoothed_index text,
    on_toronto_smoothed_sa_index text,
    on_toronto_sales_pair_count text,

    on_ottawa_index text,
    on_ottawa_sa_index text,
    on_ottawa_smoothed_index text,
    on_ottawa_smoothed_sa_index text,
    on_ottawa_sales_pair_count text,

    qc_montreal_index text,
    qc_montreal_sa_index text,
    qc_montreal_smoothed_index text,
    qc_montreal_smoothed_sa_index text,
    qc_montreal_sales_pair_count text,

    qc_quebec_city_index text,
    qc_quebec_city_sa_index text,
    qc_quebec_city_smoothed_index text,
    qc_quebec_city_smoothed_sa_index text,
    qc_quebec_city_sales_pair_count text,

    ns_halifax_index text,
    ns_halifax_sa_index text,
    ns_halifax_smoothed_index text,
    ns_halifax_smoothed_sa_index text,
    ns_halifax_sales_pair_count text
);

DROP TABLE IF EXISTS raw.city_house_real_prices;
CREATE TABLE raw.city_house_real_prices (
    city text,
    month_date TEXT,
    
    composite_hpi_sa NUMERIC,
    single_family_hpi_sa NUMERIC,
    one_storey_hpi_sa NUMERIC,
    two_storey_hpi_sa NUMERIC,
    townhouse_hpi_sa NUMERIC,
    apartment_hpi_sa NUMERIC,

    composite_benchmark_sa numeric,
    single_family_benchmark_sa numeric,
    one_storey_benchmark_sa numeric,
    two_storey_benchmark_sa numeric,
    townhouse_benchmark_sa numeric,
    apartment_benchmark_sa numeric
);

DROP TABLE IF EXISTS raw.tmp_house_price;
CREATE TABLE raw.tmp_house_price (
    month_date TEXT,

    composite_hpi_sa NUMERIC,
    single_family_hpi_sa NUMERIC,
    one_storey_hpi_sa NUMERIC,
    two_storey_hpi_sa NUMERIC,
    townhouse_hpi_sa NUMERIC,
    apartment_hpi_sa NUMERIC,
    
    composite_benchmark_sa numeric,
    single_family_benchmark_sa numeric,
    one_storey_benchmark_sa numeric,
    two_storey_benchmark_sa numeric,
    townhouse_benchmark_sa numeric,
    apartment_benchmark_sa numeric
);


DROP TABLE IF EXISTS raw.sp500_raw;
CREATE TABLE raw.sp500_raw (
    price_date text,
    close_price text,
    adj_close_price text,
    high_price text,
    low_price text,
    open_price text,
    volume text
);

DROP TABLE IF EXISTS raw.tsx_raw;
CREATE TABLE raw.tsx_raw (
    price_date text,
    open_price text,
    high_price text,
    low_price text,
    close_price text,
    adj_close_price text,
    volume text
);

DROP TABLE IF EXISTS raw.vt_raw;    
CREATE TABLE raw.vt_raw (
    price_date text,
    open_price text,
    high_price text,
    low_price text,
    close_price text,
    adj_close_price text,
    volume text
);

DROP TABLE IF EXISTS raw.city_rent_raw;
CREATE TABLE raw.city_rent_raw (
    city text,
    rent_period text,
    studio_rent text,
    studio_flag text,
    one_bedroom_rent text,
    one_bedroom_flag text,
    two_bedroom_rent text,
    two_bedroom_flag text,
    three_bedroom_plus_rent text,
    three_bedroom_plus_flag text,
    total_rent text,
    total_flag text
);

DROP TABLE IF EXISTS raw.tmp_rent_raw;  
CREATE TABLE raw.tmp_rent_raw (
    rent_period text,
    studio_rent text,
    studio_flag text,
    one_bedroom_rent text,
    one_bedroom_flag text,
    two_bedroom_rent text,
    two_bedroom_flag text,
    three_bedroom_plus_rent text,
    three_bedroom_plus_flag text,
    total_rent text,
    total_flag text
);

DROP TABLE IF EXISTS raw.canada_cpi_raw;    
CREATE TABLE raw.canada_cpi_raw (
    cpi_period text,
    cpi_value text
);

DROP TABLE IF EXISTS raw.usd_cad_raw;   
CREATE TABLE raw.usd_cad_raw (
    observation_date text,
    dexcaus text
);

DROP TABLE IF EXISTS raw.canada_5yearmortgage_raw;    
CREATE TABLE raw.canada_5yearmortgage_raw (
    mortgage_period text,
    mortgage_rate text
);