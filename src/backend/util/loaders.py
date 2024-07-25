import pandas as pd
import numpy as np
from comms.valkey import get_output_frame, set_output_frame, get_processed_files, set_processed_files
from comms.valkey import key_exists
from comms.s3 import copy_from_s3
from util.logs import get_logger

log = get_logger()

def init_frame():
   return

def init_outputs(valkey_keys, prefix):
   files_key = valkey_keys['files_key']
   output_key = valkey_keys['output_key']
   if not key_exists(files_key):
      set_processed_files(files_key, [])
   if not key_exists(output_key):
      df = init_frame()
      set_output_frame(output_key, df)

def ingest_files(files, files_key, output_key, data_dir):
   return
