import os
import sys
import shutil
import time
import traceback
import argparse
import pandas as pd
from comms.valkey import get_json_data, set_json_data, publish_message
from comms.s3 import get_objects, copy_from_s3
from comms.lfai import dummy_transcribe, inference
from util.logs import get_logger, setup_logging
from util.loaders import init_outputs, push_data, format_timediff
from util.objects import MetricTracker, CurrentState
from pathlib import Path

log = get_logger()

MESSAGE_CHANNEL = os.environ.get('SUB_CHANNEL', 'events')
STALLED = 300

def get_valkey_keys(prefix, run_id):
   return {
      'files_key': f'{prefix}_processed_files',
      'output_key': f'{run_id}_output',
      'metrics_key': f'{run_id}_metrics'
         }

def get_files_to_process(file_key, bucket, prefix=""):
   """Returns a list of files to process
      :param file_key: key in valkey where the processed files are stored
      :param bucket: Name of bucket to get objects from
      :param prefix: Checks for new files that begin with prefix
      :returns: List of file keys in s3
   """
   processed_files = get_json_data(file_key)
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
   """Creates the tmp directory to download files from s3
      :param prefix: s3 prefix where the files are uploaded
      :returns: string path to the tmp folder
   """
   data_dir = os.environ.get('DATA_DIR', '/tmp/data/')
   data_dir += prefix.replace('/', '_')
   Path(data_dir).mkdir(parents=True, exist_ok=True)
   return data_dir

def get_audio_metadata(key):
   return pd.Timestamp('now').str

def ingest_file(key: str,
                valkey_keys: dict,
                data_dir: str,
                metrics: MetricTracker,
                bucket: str):
   new_path = data_dir + key.split('/')[-1]
   success = copy_from_s3(bucket, key, new_path)
   if not success:
      log.warning(f'Skipping key {key}: could not copy from s3')
      return False
   start_time, end_time, track = get_audio_metadata(key)
   result = dummy_transcribe(new_path)
   tokens = result['performanceMetrics']['tokens']
   seconds = result['performanceMetrics']['timeToTranscribe']
   txt = ' '.join(result['transcriptions'])
   metrics.update_transcriptions(seconds, tokens)
   os.remove(new_path)
   return txt, metrics

def ingest_loop(bucket, prefix, valkey_keys, data_dir):
   num_no_updates = 0
   metrics = MetricTracker()
   current_state = CurrentState.pre_trial_start.value
   while num_no_updates < STALLED:
      files_key = valkey_keys['files_key']
      files = get_files_to_process(files_key, bucket, prefix)
      if len(files) == 0:
         num_no_updates += 1
         time.sleep(20)
         continue
      num_no_updates = 0
      processed_files = get_json_data(files_key)
      data = {}
      for key in files:
         start_time, end_time, track = get_audio_metadata(key)
         txt, metrics = ingest_file(key, valkey_keys, data_dir,
                              metrics, bucket)
         if start_time not in data:
            data[start_time] = {
               "start_time":start_time,
               "end_time":end_time,
               f"track{track}":txt
            }
         else:
            to_append = data[start_time]
            to_append[f"track{track}"] = txt
            data[start_time] = to_append
         processed_files.append(key)
         set_json_data(files_key, processed_files)
      for k, v in data.items():
         data[k] = inference(current_state, v)
         metrics.update_inferences(v["inference_seconds"])
      push_data(data, metrics, valkey_keys)
      time.sleep(20)

def cleanup(data_dir):
   if os.path.exists(data_dir):
      shutil.rmtree(data_dir)

def ingest_data(bucket, prefix, run_id):
   #setup
   try:
      valkey_keys = get_valkey_keys(prefix, run_id)
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
      ingest_loop(bucket, prefix, run_id, valkey_keys, data_dir)
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
   parser = argparse.ArgumentParser(description="postional args: bucket, prefix, run_id")
   parser.add_argument('bucket', help="s3 bucket name")
   parser.add_argument('prefix', help="s3 key prefix to check")
   parser.add_argument('run_id', help="run_id to help keep data stored separately")
   args = parser.parse_args()
   ingest_data(args.bucket, args.prefix, args.test)
