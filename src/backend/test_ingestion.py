import pandas as pd
from comms.s3 import upload_file, READ_BUCKET, get_objects, delete_key
from util.logs import setup_logging, get_logger
from util.loaders import get_prefix, get_valkey_keys, wipe_data
import time
from subprocess import Popen

log = get_logger()

def upload_dummy_data(prefix):
   for i in range(20):
      for track in range(4):
         track += 1
         ts = pd.Timestamp('now')
         y = ts.year
         m = ts.month
         d = ts.day
         h = ts.hour
         min = ts.minute
         sec = ts.second
         key = f"{prefix}track{track}/{y}-{m:02d}-{d:02d} {h:02d}-{min:02d}-{sec:02d}_track{track}.mp3"
         upload_file("test/test_data.txt", key, READ_BUCKET)
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
   #wipe_data(prefix, 1)
   #clear_s3()
   #spawn_ingestion(prefix)
   log.info("process spawned")
   upload_dummy_data(prefix)
