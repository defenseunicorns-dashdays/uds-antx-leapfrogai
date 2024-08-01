import os
import sys
import shutil
import time
import traceback
import argparse
import pandas as pd
from comms.valkey import get_json_data, set_json_data, publish_message, STATUS_KEY, TIME_ZONE
from comms.s3 import get_objects, copy_from_s3
from comms.lfai import build_transcribe_request, chat_completion
from util.logs import get_logger, setup_logging
from util.loaders import init_outputs, push_data, get_valkey_keys, test_update
from util.loaders import push_logs, get_current_state, TIME_ZONE
from util.objects import MetricTracker, CurrentState
from pathlib import Path

log = get_logger()

MESSAGE_CHANNEL = os.environ.get('SUB_CHANNEL', 'events')
STALLED = 300

def get_files_to_process(file_key, bucket, prefix=""):
   """Returns a list of files to process
      :param file_key: key in valkey where the processed filtmp/data/es are stored
      :param bucket: Name of bucket to get objects from
      :param prefix: Checks for new files that begin with prefix
      :returns: List of file keys in s3
   """
   processed_files = get_json_data(file_key)
   file_list = get_objects(prefix, bucket)
   to_process = []
   for filename in file_list:
      if filename not in processed_files:
         to_process.append(filename)
         if "track2" in filename:
            processed_files.append(filename)
   set_json_data(file_key, processed_files)
   return to_process

def send_sos(prefix, bucket,run_id, trc, restart):
   """Sends a message before the process dies
      :param prefix: process key
      :param bucket: S3 bucket where ingestion files are
      :param run_id: Current run_id
      :param trc: Traceback (if available)
      :param restart: Whether to restart the process
      :returns: None
   """
   data = {'message_type':'error', 'prefix':prefix,
           'bucket':bucket, 'run_id': run_id,
           'traceback': trc, 'restart': restart}
   publish_message(MESSAGE_CHANNEL, data)
   status = {"run_id":int(run_id), "prefix":prefix, "status":"Exiting"}
   set_json_data(STATUS_KEY, status)

def setup_ingestion(prefix):
   """Creates the tmp directory to download files from s3
      :param prefix: s3 prefix where the files are uploaded
      :returns: string path to the tmp folder
   """
   data_dir = os.environ.get('DATA_DIR', './test/')
   data_dir += prefix.replace('/', '_')
   Path(data_dir).mkdir(parents=True, exist_ok=True)
   log.info(f"{data_dir} created for audio files")
   return data_dir

def get_audio_metadata(key):
   splits = key.split('/')
   Y, M, D, track, fname = splits[1:6]
   h,m,s = fname.split(" ")[-1].split("-")[0:3]
   s = s.split("_")[0]
   start_time = pd.Timestamp(f"{Y}/{M}/{D} {h}:{m}:{s}", tz=TIME_ZONE)
   end_time = start_time + pd.Timedelta(seconds=67)
   return start_time, end_time, track

def ingest_file(key: str,
                data_dir: str,
                metrics: MetricTracker,
                bucket: str):
   new_path = data_dir + key.split('/')[-1]
   success = copy_from_s3(bucket, key, new_path)
   if not success:
      log.warning(f'Skipping key {key}: could not copy from s3')
      return False
   result = build_transcribe_request(new_path)
   log.info(result)
   perf = result["performanceMetrics"]
   tokens = perf["tokens"]
   seconds = perf['timeToTranscribe']
   txt = ' '.join(result['transcription'])
   metrics.update_transcriptions(seconds, tokens)
   os.remove(new_path)
   return txt, metrics

def get_start_times(keys, current_state, delay_type):
   data = dict()
   start_times = []
   for key in keys:
      start_time, end_time, track = get_audio_metadata(key)
      if track == "track2":
         continue
      if start_time not in data:
         start_times.append(start_time)
         data[start_time] = {
            "start_time": start_time,
            "end_time": end_time,
            track: key,
            "state": current_state,
            "delay_type": delay_type
         }
      else:
         to_append = data[start_time]
         to_append[track] = key
         data[start_time] = to_append
   return data, sorted(start_times)

def process_batch(keys: list, valkey_keys:dict, bucket:str,
                  metrics: MetricTracker, data_dir:str)->dict:
   """Processes a batch of new S3 keys
   :param keys: List of keys (strings)
   :param valkey_keys: Dictionary of keys for interacting with valkey
   :param bucket: S3 bucket name to pull from
   :param metrics: MetricTracker for current run
   :param data_dir: str path to the tmp directory to store audio files
   :returns None:
   :data_dict: Dictionary with the following stucture:
      {
         start_time: datetime64[ns]
         end_time: datetime64[ns]
         track#: string of transcription for that track (multiple tracks)
         state: string of current state
         delay_type: the type of delay
      }
   """
   processed_files = get_json_data(valkey_keys['files_key'])
   log.info(f"Keys to process: {len(keys)}")
   data = {}
   current_state, delay_type = get_current_state(valkey_keys)
   data, start_times = get_start_times(keys, current_state, delay_type)
   log.info(f"{data}")
   log.info(f"{start_times}")
   for start_time in start_times:
      data_dict = data[start_time]
      data_dict["state"] = current_state
      data_dict["delay_type"] = delay_type
      batch_files = []
      for key, value in data_dict.items():
         if key.startswith("track"):
            batch_files.append([key, value])
      for track, key in batch_files:
         try:
            txt, metrics = ingest_file(key, data_dir,
                                 metrics, bucket)
            log.debug(f"{key}:{txt}")
         except Exception as e:
            log.warning(f'Error transcribing key {key}: {e}')
            log.warning(traceback.format_exc())
            txt = ""
         data_dict[track] = txt
         processed_files.append(key)
      try:
         if current_state == CurrentState.pre_trial_start.value:
            current_state = CurrentState.trial_start.value
            data_dict["state"] = current_state
         data_dict = chat_completion(data_dict)
         current_state = data_dict["state"]
         delay_type = data_dict["delay_type"]
         metrics.update_inferences(data_dict["inference_seconds"])
      except Exception as e:
         log.warning(f'Error inferring with data {data_dict}: {e}')
         log.warning(traceback.format_exc())
         data_dict["time_to_change"] = "00:00"
         data_dict["inference_seconds"] = 0
      set_json_data(valkey_keys["files_key"], processed_files)
      push_data({start_time:data_dict}, metrics, valkey_keys)
      push_logs(valkey_keys["output_key"])
   return metrics

def ingest_loop(bucket, prefix, valkey_keys, data_dir):
   num_no_updates = 0
   metrics = MetricTracker()
   while num_no_updates < STALLED:
      files = get_files_to_process(valkey_keys['files_key'], bucket, prefix)
      if len(files) == 0:
         num_no_updates += 1
         log.info(f"No new S3 keys to be processed")
         time.sleep(10)
         # if num_no_updates == 1:
         #    push_logs(valkey_keys["output_key"])
         continue
      num_no_updates = 0
      metrics = process_batch(files, valkey_keys,
                           bucket, metrics, data_dir)

def test_loop(bucket, prefix, valkey_keys, data_dir):
   iteration = 0
   while True:
      test_update(valkey_keys["output_key"], valkey_keys["metrics_key"])
      iteration += 1
      push_logs(valkey_keys["output_key"])
      time.sleep(62)

def cleanup(data_dir):
   if os.path.exists(data_dir):
      shutil.rmtree(data_dir)

def ingest_data(bucket, prefix, run_id):
   #setup
   try:
      valkey_keys = get_valkey_keys(prefix, run_id)
      log.debug(f"valkey_keys: {valkey_keys}")
      data_dir = setup_ingestion(prefix)
   except Exception as e:
      log.warning(f'Error with ingestion setup: {e}')
      trc = traceback.format_exc()
      cleanup(data_dir)
      send_sos(prefix, bucket, run_id, trc, False)
      sys.exit(1)

   #ingestion
   try:
      ingest_loop(bucket, prefix, valkey_keys, data_dir)
   except Exception as e:
      log.warning(f'Error with ingestion loop: {e}')
      trc = traceback.format_exc()
      cleanup(data_dir)
      send_sos(prefix, bucket, run_id, trc, False)
      sys.exit(1)

   log.info(f'Ingestion stalled due to {STALLED} updates with no new files')
   cleanup(data_dir)
   send_sos(prefix, bucket, run_id, "", False)

if __name__ == '__main__':
   setup_logging()
   parser = argparse.ArgumentParser(description="postional args: bucket, prefix, run_id")
   parser.add_argument('bucket', help="s3 bucket name")
   parser.add_argument('prefix', help="s3 key prefix to check")
   parser.add_argument('run_id', type=int, help="run_id to help keep data stored separately")
   args = parser.parse_args()
   log.info(f"Spawned ingestion with args: {args}")
   ingest_data(args.bucket, args.prefix, args.run_id)
