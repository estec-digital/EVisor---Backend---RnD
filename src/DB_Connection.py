import psycopg2
import os

def get_postgres_connection(POSTGRESQL_SERVER: str, POSTGRES_PORT_EXTERNAL: str, POSTGRES_DB: str, POSTGRES_USER: str, POSTGRES_PASSWORD: str):
    """Establish a connection to the PostgreSQL database using environment variables.
    Args:
        POSTGRESQL_SERVER (str): Hostname of the PostgreSQL server.
        POSTGRES_PORT_EXTERNAL (str): External port of the PostgreSQL server.
        POSTGRES_DB (str): Name of the PostgreSQL database.
        POSTGRES_USER (str): Username for the PostgreSQL database.
        POSTGRES_PASSWORD (str): Password for the PostgreSQL database.
    Returns:
        psycopg2.extensions.connection: A connection object to the PostgreSQL database.
    """
    conn = psycopg2.connect(
        host=os.getenv("POSTGRESQL_SERVER"),
        port=os.getenv("POSTGRES_PORT_EXTERNAL"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    return conn