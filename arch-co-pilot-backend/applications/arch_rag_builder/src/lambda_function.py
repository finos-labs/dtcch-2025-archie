import json
import boto3
import logging
import pandas as pd
import yaml
from common.embbed_docs import MultimodalEmbeding
from store_embeddings import StoreEmbeddings
from common.s3_interface import S3Interface
from common.utils import timeit, load_config
from common.pgvector_interface import PGVectorInterface


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

common_config = load_config("common/config.yaml")
app_config = load_config("./config.yaml")
config = {**common_config, **app_config}

print(f"config --- \n {config}")


s3_c = boto3.client('s3')
bedrock_runtime = boto3.client(service_name='bedrock-runtime')
rds_client = boto3.client('rds-data')



def lambda_handler(event, context):
    
    print(event)
    
  
    s3_obj = S3Interface(s3_c, config)
    
    s3_record = event['Records'][0] 
    #for sqs evnts
    s3_record = json.loads(s3_record['body'])
    print(f's3_record {s3_record}')
    
    s3_record = s3_record['Records'][0]
    print(f's3_record1 {s3_record}')
    #for sqs evnts 

    doc_bucket = s3_record['s3']['bucket']['name']
    doc_key = s3_record['s3']['object']['key']
    print(f"doc_bucket --> {doc_bucket}; doc_key --> {doc_key}") 
    file_name = doc_key.split('/')[-1]
    s3_pdf_path = 's3://' + doc_bucket + '/' + doc_key
    s3_output_folder = 's3://' + doc_bucket.replace('input','output') + '/' + doc_key.replace('current','rag-images').replace(file_name, '')
  
    
    print(f"s3_pdf_path --> {s3_pdf_path} \n s3_output_folder -> {s3_output_folder}")
    
    
    store_embeddings = StoreEmbeddings(s3_c,bedrock_runtime, rds_client, config, s3_pdf_path,s3_output_folder)


    delete_existing_recs = store_embeddings.delete_related_tables_records(store_embeddings.main_doc_table, store_embeddings.embedding_tables,'document_filename', store_embeddings.document_filename)
    
    records = store_embeddings.store_doc_details()
    records = store_embeddings.main_embedding()
    records = store_embeddings.search_embedding()
    s3_obj = S3Interface(s3_c,config)
    s3_obj.delete_s3_object(doc_bucket, doc_key)

   
    