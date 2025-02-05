import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import os


# docker run -it  --network=docker_sql_default ingest-script  --user=root  --password=root  --host=pgdatabase  --port=5432  --db=ny_taxi --table_name=yellow_taxi_trips --url=${URL}
# Database configuration
DB_NAME = 'emissions_db'
DB_USER = 'root'
DB_PASSWORD = 'root'
DB_HOST = 'pgdatabase'
DB_PORT = '5432'

# Paths to data files
FILES = ['file1.csv', 'file2.csv', 'file3.csv']

# Standardize column names
STANDARD_COLUMNS = ['activity_name', 'sector', 'category', 'unit', 'kgCO2e', 'kgCO2', 'kgCH4', 'kgN2O', 'assessment_report', 'scope', 'lca', 'validity_year', 'region']


def create_database():
    conn = psycopg2.connect(dbname='postgres', user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    conn.autocommit = True
    cursor = conn.cursor()
    print(f"Attempting to drop database: {DB_NAME}")  # Print before dropping
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    print(f"Attempting to create database: {DB_NAME}") # Print before creating
    cursor.execute(f"CREATE DATABASE {DB_NAME}")
    conn.close()
    print(f"Database {DB_NAME} created!")


def create_tables():
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
    print(f"Connection string: {engine.url}") #Print the connection string
    with engine.connect() as connection:
        with open('create_emissions_tables.sql', 'r') as sql_file:
            #connection.execute(sql_file.read())
            sql = sql_file.read()

        # Split the SQL string into individual statements (split by ";")
        statements = sql.split(";")

        for statement in statements:
            statement = statement.strip()  # Remove leading/trailing whitespace
            if statement:  # Skip empty statements
                connection.execute(text(statement))  # Use text() for each statement

    print("Tables created!")


def clean_and_load_data():
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

    all_data = []

    for file in FILES:
        df = pd.read_csv(file)
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
        df = df.rename(columns={
            'emission_(kgco2e)': 'kgco2e',
            'life_cycle_assesment': 'lca',
            'year_valid_from': 'validity_year',
            'validity_region': 'region'
        })

        df['file_name'] = file
        df = df.reindex(columns=STANDARD_COLUMNS + ['file_name'])
        all_data.append(df)

    combined_df = pd.concat(all_data)
    combined_df.to_sql('emission_factors', con=engine, if_exists='append', index=False)
    print("Data loaded into the database!")


def export_approved_data():
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
    query = """SELECT * FROM emission_factors WHERE review_status_id = (SELECT id FROM review_status WHERE status = 'approved')"""
    approved_data = pd.read_sql(query, engine)
    approved_data.to_csv('approved_emission_factors.csv', index=False)
    print("Approved data exported to CSV!")


def main():
    create_database()
    create_tables()
    #clean_and_load_data()
    #export_approved_data()


if __name__ == "__main__":
    main()