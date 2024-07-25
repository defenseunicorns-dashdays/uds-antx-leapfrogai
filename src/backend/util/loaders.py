import pandas as pd
import numpy as np
from comms.valkey import get_output_frame, set_output_frame, get_processed_files, set_processed_files
from comms.valkey import key_exists
from util.logs import get_logger

log = get_logger()

def init_frame():
   return

def push_data(text, data, valkeys):
   return

def format_timediff(seconds):
   fmt_seconds = seconds % 60
   minutes = seconds // 60
   fmt_minutes = minutes % 60
   hours = minutes // 60
   print(hours, fmt_minutes, fmt_seconds)
   return "{:02d}:{:02d}:{:02d}".format(hours,fmt_minutes,fmt_seconds)

def init_outputs(valkey_keys, prefix):
   files_key = valkey_keys['files_key']
   output_key = valkey_keys['output_key']
   if not key_exists(files_key):
      set_processed_files(files_key, [])
   if not key_exists(output_key):
      df = init_frame()
      set_output_frame(output_key, df)
