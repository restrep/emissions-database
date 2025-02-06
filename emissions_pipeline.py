import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
from sqlalchemy import create_engine, text
import os
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.set_option("future.no_silent_downcasting", True)


# Database configuration
DB_NAME = "emissions_db"
DB_USER = "root"
DB_PASSWORD = "root"
DB_HOST = "pgdatabase"
DB_PORT = "5432"

# Standardize column names
STANDARD_COLUMNS = ['activity_name', 'sector', 'category', 'unit', 'kgco2e', 'kgco2', 'kgch4', 'kgn2o',
       'assesment_report', 'scope', 'lca', 'validity_year',
       'region', 'source', 'file_type']

paths = ["data-raw/S1/File 1-1.xlsx", "data-raw/S2/File 2-1.csv", "data-raw/S3/File 3-1.xlsx"]


def create_database():
    conn_admin = psycopg2.connect(dbname="postgres", user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    conn_admin.autocommit = True
    cursor = conn_admin.cursor()

    try:
        cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    except Exception as e:
        print(e)

    try:
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
    except Exception as e:
        print(e)

    conn_admin.close()
    print(f"Database {DB_NAME} created!")


def create_tables(conn):
    with open("create_emissions_tables.sql", "r") as file:
        sql = file.read()
    with conn.cursor() as cursor:
        cursor.execute(sql)
    conn.commit()
    print("Tables created successfully!")


def read_and_clean_data(paths_to_data):
    # paths_to_data is of the form ["data-raw/S1/File 1-1.xlsx","data-raw/S2/File 2-1.csv", "data-raw/S3/File 3-1.xlsx"]
    all_data = []
    for file_path in paths_to_data:
        extension = file_path.split(".")[1]
        source = file_path.split("/")[1]
        if extension == "csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # Split Sector-Category
        if source == "S1":
            df[["Sector", "Category"]] = df["Sector-Category"].str.split("/", expand=True)
            df.drop(["Sector-Category"], axis=1, inplace=True)

        # Standarize columns
        df.columns = df.columns.str.lower().str.rstrip().str.replace(" ", "_").str.replace("-", "_")
        df = df.rename(
            columns={
                "emmision_(kgco2e)": "kgco2e",
                "life_cylce_assesment": "lca",
                "year_valid_from": "validity_year",
                "validity_region": "region",
            }
        )
        # add source file and file_type
        df["source"] = source
        df["file_type"] = extension

        # clean strings to avoid duplicates like Transport and transport
        for column in ["sector", "category", "unit", "scope", "lca"]:  # Open question: activity_name ????
            df[column] = df[column].apply(lambda x: str(x).lower().rstrip())

        # rounding
         df[['kgco2e', 'kgco2', 'kgch4', 'kgn2o']] = df[['kgco2e', 'kgco2', 'kgch4', 'kgn2o']].round(5)
        # clean missing values
        df.replace(["unknown", "Unknown"], None, inplace=True)
        df.replace(["not_supplied", "not-supplied"], np.nan, inplace=True)

        df = df.reindex(columns=STANDARD_COLUMNS)  # reorder
        all_data.append(df)
    print("data clean successful")
    return pd.concat(all_data)


def insert_activities(conn, df):
    cursor = conn.cursor()
    # Get unique combinations of activity_name, sector, and category
    activities_df = df[["activity_name", "sector", "category"]].drop_duplicates()
    # Prepare data for insertion
    activities_data = [(row["activity_name"], row["sector"], row["category"]) for _, row in activities_df.iterrows()]

    # Insert data (without RETURNING)
    query = "INSERT INTO activities (activity_name, sector, category) VALUES %s"
    execute_values(cursor, query, activities_data)

    # Fetch the inserted IDs
    cursor.execute("SELECT activity_id, activity_name FROM activities")
    activity_mapping = {name: id for id, name in cursor.fetchall()}

    conn.commit()
    print("activities inserted")
    return activity_mapping


def insert_regions(conn, df):
    cursor = conn.cursor()
    # Get unique regions
    regions = df["region"].unique()
    regions_data = [(region,) for region in regions]

    query = """
        INSERT INTO regions (name)
        VALUES %s
    """
    execute_values(cursor, query, regions_data)

    # Fetch the inserted IDs
    cursor.execute("SELECT region_id, name FROM regions")
    region_mapping = {name: id for id, name in cursor.fetchall()}

    conn.commit()
    print("regions inserted")
    return region_mapping


def insert_sources(conn, df):
    cursor = conn.cursor()
    # Get unique sources
    sources_df = df[["source", "file_type"]].drop_duplicates()
    sources_data = [
        (row["source"], "Description for " + row["source"], row["file_type"]) for _, row in sources_df.iterrows()
    ]

    query = """
        INSERT INTO sources (source_name, source_description, file_type)
        VALUES %s
    """
    execute_values(cursor, query, sources_data)

    # Fetch the inserted IDs
    cursor.execute("SELECT source_id, source_name FROM sources")
    source_mapping = {name: id for id, name in cursor.fetchall()}

    conn.commit()
    print("sources inserted")
    return source_mapping


def insert_units(conn, df):
    cursor = conn.cursor()
    # Get unique units
    units = df["unit"].unique()
    units_data = [(unit, "Description for " + unit) for unit in units]

    query = """INSERT INTO units (name, description) VALUES %s """
    execute_values(cursor, query, units_data)

    # Fetch the inserted IDs
    cursor.execute("SELECT unit_id, name FROM units")
    unit_mapping = {name: id for id, name in cursor.fetchall()}

    conn.commit()
    print("units inserted")
    return unit_mapping


def insert_status(conn):
    cursor = conn.cursor()

    status_data = [
        ("pending_review", "Pending review by user"),
        ("approved", "Approved by user"),
        ("rejected", "Rejected user"),
    ]

    query = """INSERT INTO status (name, description) VALUES %s"""
    execute_values(cursor, query, status_data)

    cursor.execute("SELECT status_id, name FROM status")
    status_mapping = {name: id for id, name in cursor.fetchall()}

    conn.commit()
    print("status inserted")
    return status_mapping

def insert_sample_users(conn):
    cursor = conn.cursor()
    
    sample_users = [
        ('john', 'john@example.com', 'editor'),
        ('sarah', 'sarah@example.com', 'reviewer'),
        ('mike', 'mike@example.com', 'admin')
    ]
    
    query = """
        INSERT INTO users (username, email, role)
        VALUES %s
    """
    execute_values(cursor, query, sample_users)

    cursor.execute("SELECT user_id, username FROM users")
    user_mapping = {username: id for id, username in cursor.fetchall()}
    
    conn.commit()
    return user_mapping


def insert_emission_factors(conn, df, mappings):
    cursor = conn.cursor()
    print("inserting emissions data")
    # Prepare data for insertion
    emission_factors_data = []
    for _, row in df.iterrows():
        emission_factors_data.append(
            (
                mappings["activities"][row["activity_name"]],
                mappings["units"][row["unit"]],
                mappings["regions"][row["region"]],
                mappings["sources"][row["source"]],
                row["scope"],
                row["assesment_report"],
                row["validity_year"],
                row["lca"],
                row["kgco2e"],
                row["kgco2"],
                row["kgch4"],
                row["kgn2o"],
                mappings["status"]["pending_review"],  # Default status
            )
        )

    query = """
        INSERT INTO emission_factors (
            activity_id, unit_id, region_id, source_id, scope,
            assesment_report, validity_year, lca, kgco2e, kgco2,
            kgch4, kgn2o, status_id
        )
        VALUES %s;
    """

    execute_values(cursor, query, emission_factors_data)
    conn.commit()
    print("emissions inserted")
    print("Data insertion completed successfully!")


def main():

    create_database()

    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    print(f"Connected to database {DB_NAME}")
    create_tables(conn)

    df = read_and_clean_data(paths)
    print("## Inserting data into Tables ##")
    # get mapping and insert dimension tables
    mappings = {
        "activities": insert_activities(conn, df),
        "regions": insert_regions(conn, df),
        "sources": insert_sources(conn, df),
        "units": insert_units(conn, df),
        "status": insert_status(conn),
    }

    insert_emission_factors(conn, df, mappings)

    conn.close()


if __name__ == "__main__":
    main()


# docker build -t ingest-script .
# docker run -it --network=emissions-database_default ingest-script
