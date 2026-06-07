# imports
import requests
import pandas as pd
from io import StringIO
import sqlalchemy
from sqlalchemy import create_engine
import psycopg2
from dotenv import load_dotenv
import os
import datetime

def get_db_credentials() -> list[str]:
    '''
    Loads the .env file and returns the list of database connection credentials.
    '''
    load_dotenv()
    host = os.getenv("DB_host")
    user = os.getenv("DB_user")
    password = os.getenv("DB_password")
    db = os.getenv("DB_name")
    port = os.getenv("DB_port")

    return [user, password, db, host, port]

def connect_to_db(user: str, password: str, host: str, db_name: str) -> sqlalchemy.engine.base.Engine:
    """
    Creates sqlalchemy engine to connect to Postgres database. 
    """
    engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}/{db_name}")
    return engine

def request_crash_data(endpoint_url: str, rows: int, last_extract_date: str) -> requests.models.Response:
    '''
    Performs an API call requesting crash data. Returns the API response.
    '''
    params = {
        "$limit" : rows,
        "$where" : f"crash_date > '{last_extract_date}'"
    }

    r = requests.get(endpoint_url, params=params)

    return r


def create_df_to_load(response: requests.models.Response) -> pd.DataFrame:
        '''
        Converts the API reponse into pandas Dataframe. 
        Creates a variable 'download_datetime' with the download datetime stamp for all rows.
        Returns the dataframe.
        '''
        data = StringIO(response.text)
        df = pd.read_csv(data)

        download_datetime = response.headers['Date']
        df['download_datetime'] = download_datetime

        return df


def load_to_db(table_name: str, df: pd.DataFrame, engine: sqlalchemy.engine.base.Engine) -> None:
    '''
    Loads the data in the dataframe to the database by appending to already existing rows - incremental load.
    '''
    df.to_sql(name=table_name, con=engine, if_exists='append', index=False)



def get_last_extract_date():

    """
    if the table exists in db:
        if download_date col exists:
            take max(download_date)
        else:
            take max(crash_date)

        transform to iso format
    else:
        skip where param in api request
    """