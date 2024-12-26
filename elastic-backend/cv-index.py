"""
Script for indexing data from cv-valid-dev.csv

References:
i. https://dylancastillo.co/posts/elasticseach-python.html
"""

import os
import sys
import logging
from dotenv import load_dotenv
from eb_utils import paths, utility_functions
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import pandas as pd


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Define paths
CA_CERT_PATH = paths.CA_CERT # Your ca.crt must be placed in ./elastic-backend folder
CONFIG_DOC = paths.CONFIG_FILE
CV_VALID_DEV_CSV = paths.CV_VALID_DEV

# Define environment variables
load_dotenv(paths.ENV_FILE)
es_username = os.environ.get("ELASTIC_USERNAME")
es_password = os.environ.get("ELASTIC_PASSWORD")

print(es_username)

# Define elastic search settings
config = utility_functions.load_yaml(CONFIG_DOC)
es_endpoint = config['elasticsearch_config']['endpoint_url']

# Data ingestion variables
index_name = config['elasticsearch_index']['name']
index_map_type = config['elasticsearch_map_type']
index_map_cols = config['elasticsearch_map_cols']


def create_index(client: Elasticsearch,
             es_index_name: str,
             type_mapping: dict,
             ) -> None:
    """
    Creates an Elasticsearch index with the specified name and mapping.

    Args:
        client (Elasticsearch): Elasticsearch client instance.
        es_index_name (str): Name of the Elasticsearch index to create.
        type_mapping (dict): Mapping schema for the index.

    Logs:
        Logs a success message upon index creation.
    """
    client.indices.create(index=es_index_name, mappings=type_mapping)
    logging.info("Index `%s` created successfully", es_index_name)

def add_bulk_data(client: Elasticsearch,
                  dataframe: pd.DataFrame,
                  col_mapping: dict
                  ) -> None:
    """
    Uploads data from a DataFrame to an Elasticsearch index in bulk.

    Args:
        client (Elasticsearch): Elasticsearch client instance.
        dataframe (pd.DataFrame): DataFrame containing the data to be indexed.
        col_mapping (dict): Mapping of Elasticsearch fields to DataFrame columns.

    Logs:
        Logs success after data upload and displays index count details.

    Raises:
        NameError: If `index_name` is not defined in the scope.
    """
    bulk_data = []
    for i, row in dataframe.iterrows():
        bulk_data.append(
            {
                "_index": index_name,
                "_id": i,
                "_source": {es_col: row[df_col] for es_col, df_col in col_mapping.items()}
            }
        )

    bulk(client, bulk_data)

    client.indices.refresh(index=index_name)
    response = client.cat.count(index=index_name, format="json")[0]

    logging.info('Data successfully created!')

    for key, val in response.items():
        logging.info("%s : %s", key, val)

def preprocess_df(path: str) -> pd.DataFrame:
    """
    Preprocesses a CSV file by cleaning and filling missing values.

    Args:
        path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Cleaned DataFrame with specified transformations.
    """
    data_frame = pd.read_csv(path)
    data_frame['generated_text'] = data_frame['generated_text'].fillna("no transcription due \
                                                        to .mp3 file issue")
    data_frame = data_frame.drop(['text', 'up_votes', 'down_votes'], axis=1)
    data_frame['duration'] = data_frame['duration'].fillna(0)
    data_frame['age'] = data_frame['age'].fillna('undisclosed')
    data_frame['gender'] = data_frame['gender'].fillna('undisclosed')
    data_frame['accent'] = data_frame['accent'].fillna('to be advised')
    return data_frame

if __name__ == "__main__":
    # Connect to cluster
    #es = Elasticsearch([es_endpoint],ca_certs = CA_CERT_PATH,basic_auth=(es_username, es_password))

    es = Elasticsearch("https://52.77.217.6:9200",
                       basic_auth=("elastic","drhWCi=oYLrMglMy4Nfd"),
                       ssl_assert_fingerprint="6D:03:24:F6:3D:C6:70:DB:9E:73:9E:5D:D6:09:A2:B9:57:95:60:BB:6F:B3:44:25:A8:B4:7A:68:03:54:5A:C4"
                       )
    
    print(es.info())

    resp = es.indices.exists(index=index_name)

    if resp:
        delete = input(f"Index `{index_name}` already exists. Delete and recreate? [Y/N]:")

        if delete == 'Y':
            es.indices.delete(index=index_name)

            # Read data into pd dataframe and apply preprocessing
            df = preprocess_df(CV_VALID_DEV_CSV)

            # data ingestion into Elastic search
            create_index(client=es, es_index_name=index_name, type_mapping=index_map_type)
            add_bulk_data(client=es, dataframe=df, col_mapping=index_map_cols)

        elif delete == 'N':
            print('Exiting programe')
            sys.exit()
        else:
            raise ValueError("Can only accept `Y` (delete and recreate index) \
                             or `N` (do not delete)")
    else:
        # Read data into pd dataframe
        df = preprocess_df(CV_VALID_DEV_CSV)

        # data ingestion into Elastic search
        create_index(client=es, es_index_name=index_name, type_mapping=index_map_type)
        add_bulk_data(client=es, dataframe=df, col_mapping=index_map_cols)
