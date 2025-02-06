# Emissions Database Pipeline

## Overview
This project sets up a PostgreSQL database to store emission factor data from multiple sources, each with different formats and structures. The pipeline processes and standardizes this data before storing it in a structured schema.


## Features
- **PostgreSQL Database Setup**: Managed via Docker and `docker-compose`.
- **Data Cleaning & Transformation**: Standardizes column names, handles missing values, and ensures data consistency.
- **Schema Design**: Implements a relational schema with normalization and review processes.
- **Automated Data Ingestion**: Reads and inserts data from various sources using Python and `pandas`.

## Files
- **Dockerfile**: Sets up a Python 3.9 environment with the necessary dependencies to run the emissions data pipeline.
- **docker-compose.yaml**: Orchestrates PostgreSQL and `pgAdmin` services.
- **create_tables.sql**: Contains SQL commands to create the database schema.
- **pipeline.py**: Python script to read, clean, and insert data into the database.
- **Data Files**: Stored in `data-raw/`, categorized by source (S1, S2, S3).

## Schema Design

The database follows a **star schema** for efficiency in querying. The primary fact table, `emission_factors`, stores numerical emission data, while dimension tables provide context.

### Tables
- **`activities`**: Stores activity names, sectors, and categories.
- **`regions`**: Defines different geographical regions.
- **`sources`**: Metadata on data sources (e.g., AWS, GCP, API, Email).
- **`units`**: Standardized measurement units.
- **`status`**: Tracks review status (pending, approved, rejected).
- **`users`**: Manages roles (editor, reviewer, admin).
- **`change_requests`**: Logs requested changes and reviews.

## Initial observations from data
- Different file_type -> data comming from different sources (S1,S2,S3)
- Different number of columns  -> S1 has 12 others 13 -> Sector-Category (S1) vs Sector and Category (S2, S3)
- Different naming of columns:
    - Emmision (kgCO2e) (S1) vs kgCO2e (S2, S3)
    - LCA (S3) vs Life Cylce Assesment (S1, S2)
    - Year Valid From (S3) vs Validity Year (S2)   -> We assume they mean the same
    - Region (S3) vs Validity Region (S1, S2)
- Emissions have missing values and values like  'not-supplied', 'not_supplied' -> we make them np.nan
- some categorical columns have missing values like: 'Unknown', 'unknown' -> we make them None/ NULL
- Data types are different -> best data_type for each column?
- activity_name: can have duplicated values -> no primary key
- sector, category, unit, scope, lca: can case duplicates like Transport vs transport... activity_name could also have it but maybe not worth changing

## Questions/Asumptions 
- We need more domain knowledge to understand relations between columns
- Who is going to use the database? for what?
- What is the priority WRITE vs READ?  (Norm vs Denorm)
- How specific should region be? continent, contry, state....
- For the units? probably could include conversion factors
- How much do we know from the source? AWS/GCP, API, email, file type, contact
- Activity looks like it has a direct relation with sector and category
- Simple star schema no need to overcomplicate
- Fact table from emissions (numerical). Dimension tables: activities, region, sources, units...



# Review Process

Create specific tables for the reviewing process in the schema.

- Tables for status, users, change_requests
- Users can have different roles (editor, reviewer, admin....)

## Review process flow

By default all entries have the status 'pending_review'

1. User identifies a change/error/issue with an emission factor
2. User can submit a request with:
    - emission_factor_id
    - proposed_changes in JSON form
    - requested_by_id
    - requested_at: This one is set automatically  
3. Another user reviews the request
    - reviewed_by_id
    - adds review_comments
    - changes to table according to JSON
    - changes status to 'aprroved' or 'rejected' 

# Schema ERD

![](schema)
