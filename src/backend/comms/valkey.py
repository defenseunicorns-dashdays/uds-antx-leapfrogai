import redis
import json
import pandas as pd
import os
from io import StringIO
from util.logs import get_logger

log = get_logger()

VALKEY_ENGINE = None

def create_valkey_connection():
   """Creates a connection to valkey using environment variables
      :returns: redis.Redis object
   """
   host = os.environ.get('REDIS_HOST')
   pwd = os.environ.get('REDIS_PASSSWORD', 'test-password')
   port = os.environ.get('REDIS_PORT', '6379')
   r = redis.Redis(host=host, port=port, password=pwd)
   VALKEY_ENGINE = r
   return r

def get_valkey_connection():
   """Attempts to retrieve the valkey connection, creates a new one if ping doesn't respond
   :returns redis.Redis object
   """
   if VALKEY_ENGINE is None:
      return create_valkey_connection()
   else:
      try:
         VALKEY_ENGINE.ping()
      except Exception as e:
         log.warn(f'Error connecting to redis: {e}')
         return create_valkey_connection()
      return VALKEY_ENGINE
   
def wipe_key(key):
   r = get_valkey_connection()
   r.delete(key)

def publish_message(channel, data):
   r = get_valkey_connection()
   r.publish(channel, json.dumps(data))
   
def get_output_frame(key):
   """Retrieves the output Pandas.DataFrame from key
      :param key: Key in valkey for the DataFrame
   """
   r = get_valkey_connection()
   data = r.get(key)
   if data is None:
      log.warn(f'{key} does not exist in valkey')
      return None
   df = pd.read_json(StringIO(data.decode('utf-8')))
   return df

def set_output_frame(key, df):
   """Stores a Pandas.DataFrame object as json text in valkey @ key
      :param key: key to store dataframe in valkey
      :param df: Pandas.DataFrame object to store
      :returns: None
   """
   r = get_valkey_connection()
   r.set(key, df.to_json())


def get_processed_files(key):
   """Restores a list of files processed in the current exercise
      :param key: Key where the list of files is stored in valkey
      :returns: list of string (object keys) in s3
   """
   r = get_valkey_connection()
   data = r.get(key)
   if data is None:
      log.warn(f'{key} does not exist in valkey')
      return None
   files = list(json.loads(data))
   return files

def set_processed_files(key, files):
   """Stores a list of processed file keys @ key in valkey
      :param key: key in valkey to store the list
      :param files: list of s3 object keys that have been processed
      :returns: None
   """
   r = get_valkey_connection()
   r.set(key, json.dumps(files))
