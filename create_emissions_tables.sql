CREATE TYPE scope_type AS ENUM ('1', '2', '3');
CREATE TYPE assesment_report_type AS ENUM ('AR4', 'AR5', 'AR6');
CREATE TYPE source_type AS ENUM ('S1', 'S2', 'S3');

CREATE TABLE IF NOT EXISTS activities (
    activity_id SERIAL PRIMARY KEY,
    activity_name VARCHAR(255) NOT NULL,
    sector VARCHAR(255),
    category VARCHAR(255)
);

-- region  here we culd have continent, contry, state....
CREATE TABLE IF NOT EXISTS regions (
    region_id SERIAL PRIMARY KEY,
    name TEXT
);

-- sources   AWS/GCP, API, email, file type, contact
CREATE TABLE IF NOT EXISTS sources (
    source_id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    source_description VARCHAR(255),
    file_type VARCHAR(50)
);

-- units tables...probably could include conversion factors
CREATE TABLE units (
    unit_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

-- user management
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- limit roles to essential types
    CONSTRAINT valid_role CHECK (role IN ('editor', 'reviewer', 'admin'))
);

-- status
CREATE TABLE IF NOT EXISTS status (
    status_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    
    CONSTRAINT valid_status_name CHECK (name IN ('pending_review', 'in_review', 'approved','rejected'))
);


-- Main emission factors table
CREATE TABLE IF NOT EXISTS emission_factors (
    emission_factor_id SERIAL PRIMARY KEY,
    activity_id INTEGER NOT NULL REFERENCES activities(activity_id),
    unit_id INTEGER NOT NULL REFERENCES units(unit_id),
    region_id INTEGER NOT NULL REFERENCES regions(region_id),
    source_id INTEGER NOT NULL REFERENCES sources(source_id),
    scope scope_type,
    assesment_report assesment_report_type,  -- maybe also a table for reports
    validity_year INTEGER,
    lca VARCHAR(100),
    kgco2e DECIMAL(20,10),
    kgco2 DECIMAL(20,10),
    kgch4 DECIMAL(20,10),
    kgn2o DECIMAL(20,10),
    status_id INTEGER NOT NULL REFERENCES status(status_id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    
);


-- change request table
CREATE TABLE IF NOT EXISTS change_requests (
    change_request_id SERIAL PRIMARY KEY,
    emission_factor_id INTEGER REFERENCES emission_factors(emission_factor_id),
    requested_by_id INTEGER NOT NULL REFERENCES users(user_id),
    reviewed_by_id INTEGER REFERENCES users(user_id),
    status_id INTEGER NOT NULL REFERENCES status(status_id),

    proposed_changes JSONB NOT NULL,
    review_comments TEXT,

    requested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP WITH TIME ZONE
    
);
