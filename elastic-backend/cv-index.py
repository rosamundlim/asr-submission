"""Script for indexing data from cv-valid-dev.csv"""

import os
import logging
import sys
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


def create_index_add_data(es: Elasticsearch,
             index_name: str,
             df: pd.DataFrame,
             type_mapping: dict,
             col_mapping: dict
             ) -> None:
    es.indices.create(index=index_name, mappings=type_mapping)

    for i, row in df.iterrows():
        doc = {es_col: row[df_col] for es_col, df_col in col_mapping.items()}
        es.index(index=index_name, id=i, document= doc)

    es.indices.refresh(index=index_name)
    response = es.cat.count(index=index_name, format="json")[0]

    for key, val in response.items():
        logging.info("%s : %s", key, val)

    # optional delete index
    es.indices.delete(index=index_name)

    logging.info('Index `%s` deleted', index_name)

if __name__ == "__main__":
    # Connect to cluster
    es = Elasticsearch([es_endpoint],
                       ca_certs = CA_CERT_PATH,
                       basic_auth=(es_username, es_password)
                       )
    print(es.info())

    resp = es.indices.exists(
    index=index_name)
    print(resp)

    sys.exit()

    print('deleted index')

    # read data into pd dataframe
    df = pd.read_csv(CV_VALID_DEV_CSV)
    df = df.fillna("NA")
    create_index_add_data(es, index_name, df, index_map_type, index_map_cols)
