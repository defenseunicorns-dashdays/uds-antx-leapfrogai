import pandas as pd
import numpy as np
import os
import argparse
from comms.valkey import get_processed_files()
from comms.s3 import get_objects
from util.logs import get_logger, setup_logging()

log = get_logger()

def get_files_to_process(prefix=""):
   """Returns a list of files to process
      :param prefix: Checks for new files that begin with prefix
      :returns: List of file keys in s3
   """
   processed_files = get_processed_files()
   file_list = get_objects(prefix)
   to_process = []
   for filename in file_list:
      if filename not in processed_files:
         to_process.append(object['Key'])
   return to_process

def ingest_data(bucket, prefix, test):
   raise NotImplementedError

if __name__ == '__main__':
   setup_logging()
   parser = argparse.ArgumentParser(description="postional args: bucket, prefix")
   parser.add_argument('bucket', help="s3 bucket name")
   parser.add_argument('prefix', help="s3 key prefix to check")
   parser.add_argument('-t', '--test', dest='test', action='store_true',
                       help='Upload fake testing data')
   args = parser.parse_args()
   ingest_data(args.bucket, args.prefix, args.test)

