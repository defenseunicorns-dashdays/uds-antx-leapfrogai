import boto3
import os
import traceback
from util.logs import get_logger

log = get_logger()

REGION = os.environ.get('S3_REGION', None)
ENDPOINT = os.environ.get('S3_ENDPOINT', 'http://localhost:9000')
WRITE_BUCKET = os.environ.get('WRITE_BUCKET', 'uds')
READ_BUCKET = os.environ.get('READ_BUCKET', 'uds')

def get_s3_client():
   """Returns boto3 s3 client from environment variables"""
   access_key = os.environ.get('S3_ACCESS_KEY', "9GHSyatJi0LlWfecGT7K")  # hardcoded Minio key for testing purposes
   secret_key = os.environ.get('S3_SECRET_KEY', "cE1buvYmHR1KEa3B4p2k1LQgvtoT9JfisvbxzYKX")  # hardcoded Minio key for testing purposes
   return boto3.client('s3', endpoint_url=ENDPOINT,
                       region_name=REGION,
                       aws_access_key_id=access_key,
                       aws_secret_access_key=secret_key)

def get_objects(prefix="", bucket=READ_BUCKET, endswith=".mp3"):
   """Returns a list of keys for objects in a bucket
      :param prefix: Filters the bucket for keys that begin with prefix
      :param bucket: Bucket to return objects of
      :param endswith: Only include keys that endswith this string
      :returns: List of file keys in the bucket
   """
   s3 = get_s3_client()
   new_files = []
   file_list = []
   continuation = None
   truncated = True
   kwargs = {"Bucket":bucket, "Prefix":prefix}
   while truncated:
      if continuation:
         kwargs["ContinuationToken"] = continuation
      try:
         response = s3.list_objects_v2(**kwargs)
      except Exception as e:
         log.warning(f'Error listing objects in {bucket}: {e}')
         log.warning(traceback.format_exc())
         return file_list
      if 'Contents' not in response:
         return file_list
      else:
         new_files = [x['Key'] for x in response['Contents'] if x['Key'].endswith(endswith)]
         file_list = file_list + new_files
         truncated = response["IsTruncated"]
         log.info(f"Keys found: {len(file_list)}, truncated:{truncated}")
         truncated = response["IsTruncated"]
         if truncated:
            continuation = response["NextContinuationToken"]
   return file_list

def upload_file(file_path, key, bucket=WRITE_BUCKET):
   """Uploads a local file to S3
        :param file_path: S3 bucket name
        :param key: key for file
        :param bucket: bucket name / ARN
        :returns: True if success | False if failed
    """
   if key is None:
      key = os.path.basename(file_path)
   s3 = get_s3_client()
   try:
      response = s3.upload_file(file_path, bucket, key)
   except Exception as e:
      log.warning(f'Error uploading {file_path} to s3://{bucket}/{key}')
      log.warning(traceback.format_exc())
      return False
   return True

def delete_key(key, bucket):
   s3 = get_s3_client()
   try:
      resp = s3.delete_object(Bucket=bucket, Key=key)
      log.info(f'{key} deleted from {bucket}')
   except Exception as e:
      log.warning(f"Error deleting {key} from s3://{bucket}")
      log.warning(traceback.format_exc())
      return False
   return True

def copy_from_s3(bucket, key, file_path):
   """Copies a file from s3
      :param bucket: S3 bucket name / ARN
      :param key: key for file
      :param file_path: local path to download to
      :returns: True if success | False if failed
   """
   try:
      log.info(f'Copying s3://{bucket}/{key} -> {file_path}')
      s3 = get_s3_client()
      s3.download_file(Bucket=bucket, Key=key, Filename=file_path)
   except Exception as e:
      log.warning(f'Error downloading S3 Object: s3://{bucket}/{key} -> {file_path}')
      log.warning(traceback.format_exc())
      return False
   return True
