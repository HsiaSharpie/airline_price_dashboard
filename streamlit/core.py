import os

from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "flights_db")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")


def get_engine(
    user,
    password,
    ip,
    port,
    database,
    connect_type, 
    connect_hive_db_type=None
):
    if connect_type == "MSSQL":
        base_connect_string = "mssql+pymssql://"
    elif connect_type == "HIVE" and connect_hive_db_type == "MySQL":
        base_connect_string = "mysql+mysqldb://"
    elif connect_type == "HIVE" and connect_hive_db_type == "PostgreSQL":
        base_connect_string = "postgresql+psycopg2://"
    elif connect_type == "HIVE" and connect_hive_db_type == "Oracle":
        base_connect_string = "oracle+oracledb://"
    elif connect_type == "POSTGRESQL":
        base_connect_string = "postgresql+psycopg2://"
    elif connect_type == "GREENPLUM":
        base_connect_string = "postgresql+psycopg2://"
    elif connect_type == "DB2":
        base_connect_string = "db2+ibm_db://"
    elif connect_type == "TRINO":
        base_connect_string = "trino://"
    
    connect_string = base_connect_string + "{user}:{password}@{ip}:{port}/{database}".format(
        user=user,
        password=password,
        ip=ip,
        port=port,
        database=database)
    return create_engine(connect_string)


def load_data(sql_script, params=None, return_type="list"):
    engine = get_engine(
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        ip=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        connect_type="POSTGRESQL",
    )
    return_list = []
    with engine.connect() as connection:
        query_result = connection.execute(text(sql_script), params)
        if query_result.returns_rows:
            keys = [x for x in query_result.keys()]
            for record in query_result:
                query_dict = {x: y for x, y in zip(keys, record)}
                return_list.append(query_dict)
    if return_type == "dataframe":
        return pd.DataFrame(return_list)
    return return_list