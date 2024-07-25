import os
import sys
import shutil
import time
import traceback
import argparse
from comms.valkey import get_processed_files, publish_message
from comms.s3 import get_objects
from util.logs import get_logger, setup_logging
from util.loaders import init_outputs, ingest_files
from pathlib import Path

log = get_logger()

MESSAGE_CHANNEL = os.environ.get('SUB_CHANNEL', 'events')
STALLED = 50

def get_valkey_keys(prefix):
   return {
      'files_key': f'{prefix}_processed_files',
      'output_key': f'{prefix}_output'
           }

def get_files_to_process(file_key, bucket, prefix=""):
   """Returns a list of files to process
      :param file_key: key in valkey where the processed files are stored
      :param bucket: Name of bucket to get objects from
      :param prefix: Checks for new files that begin with prefix
      :returns: List of file keys in s3
   """
   processed_files = get_processed_files(file_key)
   file_list = get_objects(prefix, bucket)
   to_process = []
   for filename in file_list:
      if filename not in processed_files and filename.endswith('.mp3'):
         to_process.append(object['Key'])
   return to_process

def send_sos(prefix, bucket, trc, restart):
   """Sends a message before the process dies
      :param prefix: process key
      :param bucket: S3 bucket where ingestion files are
      :param trc: Traceback (if available)
      :param restart: Whether to restart the process
      :returns: None
   """
   data = {'message_type':'error', 'prefix':prefix,
           'bucket':bucket, 'traceback': trc, 'restart': restart}
   publish_message(MESSAGE_CHANNEL, data)

def setup_ingestion(prefix):
   data_dir = os.environ.get('DATA_DIR', '/tmp/data/')
   data_dir += prefix.replace('/', '_')
   Path(data_dir).mkdir(parents=True, exist_ok=True)
   return data_dir

def ingest_loop(bucket, prefix, valkey_keys, data_dir):
   num_no_updates = 0
   while num_no_updates < STALLED:
      files_key = valkey_keys['files_key']
      output_key = valkey_keys['output_key']
      files = get_files_to_process(files_key, bucket, prefix)
      if len(files) == 0:
         num_no_updates += 1
         time.sleep(20)
         continue
      num_no_updates = 0
      ingest_files(files, files_key, output_key, data_dir)
      time.sleep(20)

def cleanup(data_dir):
   if os.path.exists(data_dir):
      shutil.rmtree(data_dir)

def ingest_data(bucket, prefix):
   #setup
   try:
      valkey_keys = get_valkey_keys(prefix)
      data_dir = setup_ingestion(prefix)
      init_outputs(valkey_keys, prefix)
   except Exception as e:
      log.warning(f'Error with ingestion setup: {e}')
      trc = traceback.format_exc()
      cleanup(data_dir)
      send_sos(prefix, bucket, trc, False)
      sys.exit(1)

   #ingestion
   try:
      ingest_loop(bucket, prefix, valkey_keys, data_dir)
   except Exception as e:
      log.warning(f'Error with ingestion loop: {e}')
      trc = traceback.format_exc()
      cleanup(data_dir)
      send_sos(prefix, bucket, trc, True)
      sys.exit(1)

   log.info(f'Ingestion stalled due to {STALLED} updates with no new files')
   cleanup(data_dir)
   send_sos(prefix, bucket, "", False)


if __name__ == '__main__':
   setup_logging()
   parser = argparse.ArgumentParser(description="postional args: bucket, prefix")
   parser.add_argument('bucket', help="s3 bucket name")
   parser.add_argument('prefix', help="s3 key prefix to check")
   args = parser.parse_args()
   ingest_data(args.bucket, args.prefix, args.test)
