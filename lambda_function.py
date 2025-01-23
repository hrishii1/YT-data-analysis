import awswrangler as wr
import pandas as pd
import urllib.parse
import os

# Read environment variables
os_input_s3_cleansed_layer = os.environ['s3_cleansed_layer']
os_input_glue_catalog_db_name = os.environ['glue_catalog_db_name']
os_input_glue_catalog_table_name = os.environ['glue_catalog_table_name']
os_input_write_data_operation = os.environ['write_data_operation']


def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    try:
        # Read JSON from S3
        df_raw = wr.s3.read_json(f"s3://{bucket}/{key}")

        # Normalize JSON to DataFrame
        df_step_1 = pd.json_normalize(df_raw['items'])

        # Sanitize the mode value and validate it
        mode = os_input_write_data_operation.strip().lower()
        valid_modes = {"append", "overwrite", "overwrite_partitions"}
        if mode not in valid_modes:
            raise ValueError(f"{mode} is an invalid mode. Please use one of: {', '.join(valid_modes)}.")

        # Write to S3 as Parquet
        wr_response = wr.s3.to_parquet(
            df=df_step_1,
            path=os_input_s3_cleansed_layer,
            dataset=True,
            database=os_input_glue_catalog_db_name,
            table=os_input_glue_catalog_table_name,
            mode=mode
        )

        return wr_response
    except Exception as e:
        print(f"Error: {e}")
        raise e
