CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    sector TEXT,
    category TEXT
);

CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    name TEXT
);

CREATE TABLE IF NOT EXISTS regions (
    id SERIAL PRIMARY KEY,
    name TEXT
);

CREATE TABLE IF NOT EXISTS review_status (
    id SERIAL PRIMARY KEY,
    status TEXT,
    reviewed_by TEXT,
    review_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS emission_factors (
    id SERIAL PRIMARY KEY,
    activity_name TEXT,
    unit TEXT,
    kgCO2e FLOAT,
    kgCO2 FLOAT,
    kgCH4 FLOAT,
    kgN2O FLOAT,
    report_id INT REFERENCES reports(id),
    scope TEXT,
    lifecycle TEXT,
    validity_year INT,
    region_id INT REFERENCES regions(id),
    category_id INT REFERENCES categories(id),
    review_status_id INT REFERENCES review_status(id),
    source_file TEXT
);