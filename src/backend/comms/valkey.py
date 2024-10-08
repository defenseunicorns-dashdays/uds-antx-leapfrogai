import redis
import json
import pandas as pd
import os
from io import StringIO
from util.logs import get_logger
from util.objects import DATETIME_FORMAT

log = get_logger()

VALKEY_ENGINE = None

TIME_ZONE = "US/Pacific"

def create_valkey_connection():
   """Creates a connection to valkey using environment variables
      :returns: redis.Redis object
   """
   host = os.environ.get('VALKEY_HOST', "localhost")
   pwd = os.environ.get('VALKEY_PASSSWORD', 'test-password')
   port = os.environ.get('VALKEY_PORT', '6379')
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
   
def key_exists(key: str):
   r = get_valkey_connection()
   return r.exists(key)
   
def wipe_key(key: str):
   r = get_valkey_connection()
   if r.exists(key):
      r.delete(key)

def publish_message(channel: str, data: dict):
   """Publishes a dictionary as a valkey message
      :param channel: string to publish dictionary to
      :param data: dictionary to publish as message
      :returns: None
   """
   log.info(f'Publishing message {data} to channel {channel}')
   r = get_valkey_connection()
   r.publish(channel, json.dumps(data))
   
def get_output_frame(key):
   """Retrieves the output Pandas.DataFrame from key
      :param key: Key in valkey for the DataFrame
      :returns: pandas.DataFrame
   """
   r = get_valkey_connection()
   data = r.get(key)
   if data is None:
      log.warn(f'{key} does not exist in valkey')
      return None
   df = pd.read_json(StringIO(data.decode('utf-8')))
   df['start'] = pd.to_datetime(df['start'])
   df['end'] = pd.to_datetime(df['end'])
   df['start'] = df['start'].dt.tz_localize(tz=TIME_ZONE)
   df['end'] = df['end'].dt.tz_localize(tz=TIME_ZONE)
   return df

def set_output_frame(key, df):
   """Stores a Pandas.DataFrame object as json text in valkey @ key
      :param key: key to store dataframe in valkey
      :param df: Pandas.DataFrame object to store
      :returns: None
   """
   df = df.sort_values('start', ascending=True, ignore_index=True)
   df['start'] = df['start'].dt.strftime(DATETIME_FORMAT)
   df['end'] = df['end'].dt.strftime(DATETIME_FORMAT)
   log.debug(f'Saving frame to {key}:\n{df.tail()}')
   r = get_valkey_connection()
   r.set(key, df.to_json())

def get_hash(channel, hash):
   r = get_valkey_connection()
   data = r.hget(channel, hash)
   if data is None:
      log.warn(f'{hash} does not exist in {channel}')
      return None
   result = json.loads(data)
   return result

def set_hash(channel, hash, value):
   r = get_valkey_connection()
   r.hset(channel, hash, value)

def get_json_data(key):
   """Gets json data stored in key
      :param key: Key where the data is stored in valkey
      :returns: list or dict of json data
   """
   r = get_valkey_connection()
   data = r.get(key)
   if data is None:
      log.warn(f'{key} does not exist in valkey')
      return []
   dict_data = json.loads(data)
   return dict_data

def set_json_data(key, data):
   """Stores json data in key
      :param key: key in valkey to store the list
      :param data: data that can be jsonified into valkey
      :returns: None
   """
   r = get_valkey_connection()
   r.set(key, json.dumps(data))
