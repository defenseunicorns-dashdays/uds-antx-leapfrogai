import pandas as pd
import numpy as np
import os
from comms.s3 import upload_file, READ_BUCKET, get_objects, delete_key
from util.logs import setup_logging, get_logger
from util.loaders import get_prefix, wipe_data
import time
from subprocess import Popen
import argparse

log = get_logger()

def upload_dummy_data(prefix, iters):
   for i in range(iters):
      choices = os.listdir("./test/audio/")
      choices = [x for x in choices if x.endswith('.mp3')]
      choices = np.random.choice(choices, 4)
      for track in range(4):
         file_path = f"./test/audio/{choices[track]}"
         track += 1
         if track == 2:
            continue
         ts = pd.Timestamp('now')
         y = ts.year
         m = ts.month
         d = ts.day
         h = ts.hour
         min = ts.minute
         sec = ts.second
         key = f"{prefix}track{track}/{y}-{m:02d}-{d:02d} {h:02d}-{min:02d}-{sec:02d}_track{track}.mp3"
         upload_file(file_path, key, READ_BUCKET)
      time.sleep(67)

def spawn_ingestion(prefix):
   run_id = 1
   bucket = READ_BUCKET
   cmd = ["python3", "ingest.py", bucket, prefix, str(run_id)]
   log.info(f'Spawning process: {cmd}')
   proc = Popen(cmd)
   return

def clear_s3():
   keys = get_objects()
   for key in keys:
      delete_key(key, READ_BUCKET)

if __name__ == '__main__':
   setup_logging()
   prefix = get_prefix()
   parser = argparse.ArgumentParser(description="testing arguments: mode can be setup, start_ingestion, start_upload")
   parser.add_argument("mode")
   args = parser.parse_args()
   mode = args.mode
   log.info(f"Running testing with mode={mode}")
   if mode == "setup":
      # wipe_data(prefix, 1)
      # clear_s3()
      upload_dummy_data(prefix, 1)
   elif mode == "start_ingestion":
      wipe_data
      spawn_ingestion(prefix)
   elif mode == "start_upload":
      upload_dummy_data(prefix, 20)
   else:
      log.info(F"Could not parse mode: {mode}")
