import pandas as pd
import yaml
import logging
import boto3
from botocore.exceptions import ClientError
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


class S3Interface():
    def __init__(self, s3_c, config):
        """
        clas to interface with s3
        """
        self.s3_c = s3_c
        self.config = config

    def parse_s3_uri(self, s3_uri):
        parsed_url = urlparse(s3_uri)
        bucket_name = parsed_url.netloc  # Extract bucket name from URI
        object_key = parsed_url.path.lstrip('/') 
        
        return bucket_name, object_key
        
        
    def read_csv_to_pd(self,s3_bucket,s3_key):
        try:
            s3_file = self.s3_c.get_object(Bucket=s3_bucket, Key=s3_key)
            pd_df = pd.read_csv(s3_file.get("Body"))
        except Exception as e:
            print(f"Failed to download file from S3: {e}")
            raise
        return pd_df
        
    def copy_object(self, src_bucket, src_key, dst_bucket, dst_key):
        try:
            response = self.s3_c.copy_object(
                Bucket=dst_bucket,
                CopySource=f'/{src_bucket}/{src_key}',
                Key=dst_key,
            )
        except Exception as e:
            print(f"Failed to copy file {src_key} from {src_bucket} to {dst_bucket} and key {dst_key} : {e}")
            raise  
        
    def delete_s3_object(self, bucket, key):
        try:
            response = self.s3_c.delete_object(
                                Bucket=bucket,
                                Key=key
                            )
        except Exception as e:
            print(f"Failed to delete file {key} from {bucket}  : {e}")
            raise  