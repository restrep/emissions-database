FROM python:3.9

RUN apt-get install wget
RUN pip install pandas sqlalchemy psycopg2

WORKDIR /app
COPY emissions_pipeline.py emissions_pipeline.py
COPY create_emissions_tables.sql create_emissions_tables.sql

ENTRYPOINT ["python", "emissions_pipeline.py"]