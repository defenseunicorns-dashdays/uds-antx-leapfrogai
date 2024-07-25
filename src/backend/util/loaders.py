import pandas as pd
import numpy as np
from comms.valkey import get_output_frame, set_output_frame, get_processed_files, set_processed_files
from comms.s3 import copy_from_s3
from util.logs import get_logger

log = get_logger()

def init_outputs(valkey_keys, prefix):
   return

def ingest_files(files, files_key, output_key, data_dir):
   return