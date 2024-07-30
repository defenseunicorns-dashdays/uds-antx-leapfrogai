import pandas as pd
import numpy as np
import os
from comms.s3 import upload_file, READ_BUCKET, get_objects, delete_key
from util.logs import setup_logging, get_logger
from util.loaders import get_prefix, wipe_data, get_current_run, parse_date
from util.loaders import init_outputs, get_valkey_keys
import time
from subprocess import Popen
import argparse

log = get_logger()

def upload_dummy_data(prefix, date, iters):
   for i in range(iters):
      choices = os.listdir("./test/audio/")
      choices = [x for x in choices if x.endswith('.mp3')]
      choices = np.random.choice(choices, 4)
      ts = pd.Timestamp('now', tz="US/Pacific")
      y = ts.year
      m = ts.month
      d = ts.day
      h = ts.hour
      if date:
         ts.replace(month=date.month)
         ts.replace(day=date.day)
      min = ts.minute
      sec = ts.second
      for track in range(4):
         file_path = f"./test/audio/{choices[track]}"
         track += 1
         key = f"{prefix}track{track}/{y}-{m:02d}-{d:02d} {h:02d}-{min:02d}-{sec:02d}_track{track}.mp3"
         upload_file(file_path, key, READ_BUCKET)
      time.sleep(30)

def spawn_ingestion(prefix, run_id):
   bucket = READ_BUCKET
   cmd = ["python3", "ingest.py", bucket, prefix, str(run_id)]
   log.info(f'Spawning process: {cmd}')
   proc = Popen(cmd)
   return

def clear_s3():
   keys = get_objects()
   if keys == None:
    return
   for key in keys:
      delete_key(key, READ_BUCKET)

if __name__ == '__main__':
   setup_logging()
   parser = argparse.ArgumentParser(description="testing arguments: mode can be setup, start_ingestion, start_upload")
   parser.add_argument("mode")
   parser.add_argument("-d", "--date", required=False, help="MMDDYYYY string")
   args = parser.parse_args()
   mode = args.mode
   date = args.date
   if date:
      date = parse_date(date)
   prefix = get_prefix(date)
   _, run_id, status = get_current_run()
   run_id = int(run_id) + 1
   log.info(f"Running testing with mode={mode}, prefix={prefix}, run_id={run_id}")
   if mode == "setup":
      wipe_data(prefix, run_id)
      clear_s3()
      valkey_keys = get_valkey_keys(prefix, run_id)
      log.info(f"{valkey_keys}")
      init_outputs(valkey_keys, date)
      upload_dummy_data(prefix, date, 1)
   elif mode == "start_ingestion":
      spawn_ingestion(prefix, run_id)
   elif mode == "start_upload":
      upload_dummy_data(prefix, date, 20)
   else:
      log.info(F"Could not parse mode: {mode}")
