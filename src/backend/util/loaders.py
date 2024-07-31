import pandas as pd
import numpy as np
import random
import string
import os
from comms.valkey import get_output_frame, set_output_frame, set_json_data
from comms.valkey import get_json_data, TIME_ZONE
from comms.valkey import key_exists, wipe_key, publish_message
from comms.s3 import WRITE_BUCKET, upload_file
from util.logs import get_logger
from util.objects import *

log = get_logger()

OUTPUT_COLUMNS = ['start', 'end', 'track1', 'track2',
                  'track3', 'track4', 'state', 'notes', 'delay type']
VALKEY_COLUMNS = OUTPUT_COLUMNS + ['seconds_to_state_change']

OUTPUT_STRING_FORMAT = "%-m/%d/%Y %-H:%M"

LOG_DIR = os.environ.get("LOG_DIR", "./")

def format_timediff(seconds, hours=True):
   fmt_seconds = seconds % 60
   minutes = seconds // 60
   fmt_minutes = minutes % 60
   hours = minutes // 60
   dt_string = "{:02d}:{:02d}:{:02d}".format(hours,fmt_minutes,fmt_seconds)
   if not hours:
      dt_string = dt_string[3:]
   return dt_string

def get_random_string(length):
   chars = random.choices(string.ascii_uppercase + string.digits, k=length)
   chars = " ".join(chars)
   return chars

def get_valkey_keys(prefix, run_id):
   return {
      'files_key': f'{prefix}_processed_files',
      'output_key': f'{prefix}_output',
      'metrics_key': f'{run_id}_metrics'
         }

def wipe_data(key_prefix, run_id):
   keys = get_valkey_keys(key_prefix, run_id)
   log.debug(f'Deleting keys: {keys}')
   for k, v in keys.items():
      wipe_key(v)

def init_frame():
   log.info(f'Initializing data frame')
   start_time = pd.Timestamp('now', tz=TIME_ZONE)
   end_time = start_time
   state = CurrentState.trial_start.value
   seconds_to_state_change = 75
   data = {
      "start":start_time,
      "end":end_time,
      "track1": "",
      "track2": "",
      "track3": "",
      "track4": "",
      "state": state,
      "notes": "",
      "delay type": "",
      "time_to_change": format_timediff(seconds_to_state_change, hours=False)
   }
   df = pd.DataFrame([data])
   df['start'] = pd.to_datetime(df['start'])
   df['start'] = pd.to_datetime(df['start'])
   return df

def get_current_state(valkeys):
   df = get_output_frame(valkeys["output_key"])
   current_state = df.loc[df["state"] != "", "state"].values[-1]
   delay_reason = df.loc[df["delay type"] != "", "delay type"]
   if delay_reason.empty:
      delay_reason = ""
   else:
      delay_reason = delay_reason.values[-1]
   return current_state, delay_reason   

def get_prefix():
   ts = pd.Timestamp("now", tz=TIME_ZONE)
   y = ts.year
   m = ts.month
   d = ts.day
   prefix = f"Distribution-Statement-D/{y}/{m:02d}/{d:02d}/"
   return prefix

#TODO: track this in valkey
def get_run_id():
   return 1

def get_current_run_id():
   return 1

def init_run():
   run_id = get_run_id()
   prefix = get_prefix()
   keys = get_valkey_keys(prefix, run_id)
   init_outputs(keys)

   #Kick off ingestion
   msg = {
      "message_type": "start",
      "bucket": os.environ.get("READ_BUCKET", "antx"),
      "prefix": prefix,
      "run_id": run_id
   }
   publish_message("events", msg)

def end_run():
   prefix = get_prefix()
   run_id = get_run_id()
   msg = {
      "message_type": "end",
      "bucket": os.environ.get("READ_BUCKET", "antx"),
      "prefix": prefix,
      "run_id": run_id
   }
   publish_message("events", msg)

def format_for_push(df: pd.DataFrame):
   df['start'] = df['start'].dt.strftime(OUTPUT_STRING_FORMAT)
   df['end'] = df['end'].dt.strftime(OUTPUT_STRING_FORMAT)
   df["next_state"] = df['state'].shift(1)
   df.loc[df['state'] == df['next_state'], 'state'] = ""
   df = df[OUTPUT_COLUMNS]
   return df

def push_logs(output_key):
   df = get_output_frame(output_key)
   start_date = df['start'].min().strftime("%Y-%-m-%-d")
   df = format_for_push(df)
   file_path = f"{LOG_DIR}{start_date}_all_tracks.csv"
   key = file_path.split("/")[-1]
   log.info(f'Saving output to {file_path} and s3://{WRITE_BUCKET}/{key}')
   df.to_csv(file_path, index=False)
   upload_file(file_path, file_path.split("/")[-1])

def append_row(frame_key, data):
   row = pd.DataFrame([data])
   row['start'] = pd.to_datetime(row['start'])
   row['end'] = pd.to_datetime(row['end'])
   df = get_output_frame(frame_key)
   df = pd.concat([df, row], ignore_index=True)
   set_output_frame(frame_key, df)

def push_metrics(metrics: MetricTracker, metric_key: str):
   data = {
      "transcription": {
         "min": metrics.min_transcription,
         "max": metrics.max_transcription,
         "avg": metrics.avg_transcription
      },
      "inference": {
         "min": metrics.min_infer,
         "max": metrics.max_infer,
         "avg": metrics.max_infer
      },
      "download": {
         "min": metrics.min_download,
         "max": metrics.max_download,
         "avg": metrics.avg_download
      }
   }
   set_json_data(metric_key, data)

def setup_metrics(metric_key):
   data = {
      "transcription": {
         "min": 0,
         "max": 0,
         "avg": 0
      },
      "inference": {
         "min": 0,
         "max": 0,
         "avg": 0
      },
      "download": {
         "min": 0,
         "max": 0,
         "avg": 0
      }
   }
   set_json_data(metric_key, data)

def push_data(data, metrics, valkeys):
   for start_time, data_dict in data.items():
      push_data = {
         "start":data_dict["start_time"],
         "end":data_dict["end_time"],
         "track1": data_dict.get("track1", ""),
         "track2": data_dict.get("track2", ""),
         "track3": data_dict.get("track3", ""),
         "track4": data_dict.get("track4", ""),
         "state": data_dict["state"],
         "notes": "",
         "delay type": data_dict.get("delay_type", ""),
         "time_to_change": data_dict["time_to_change"]
      }
      append_row(valkeys['output_key'], push_data)
   push_metrics(metrics, valkeys["metrics_key"])

def test_update(output_key, metrics_key):
   start_time = pd.Timestamp('now', tz=TIME_ZONE)
   length = random.randint(10, 30)
   change_seconds = int(np.random.normal(120, 45, 1)[0])
   push_data = {
      "start":start_time,
      "end": start_time,
      "track1": get_random_string(length),
      "track2": "",
      "track3": get_random_string(length),
      "track4": get_random_string(length),
      "state": random.choice(list(CurrentState)).value,
      "notes": "",
      "delay type": "",
      "time_to_change": format_timediff(change_seconds, hours=False)
   }
   if push_data["state"].startswith("Delay"):
      push_data["delay type"] = random.choice(list(DelayReason)).value
      log.debug(f"Delay Start substate: {push_data['delay type']}")
   append_row(output_key, push_data)
   metrics = MetricTracker()
   data = np.random.normal(7,1,6)
   metrics.min_infer = data[0]
   metrics.max_infer = data[1]
   metrics.avg_infer = data[2]
   metrics.max_transcription = data[3]
   metrics.min_transcription = data[4]
   metrics.avg_infer = data[5]
   push_metrics(metrics, metrics_key)

def init_outputs(valkey_keys):
   files_key = valkey_keys['files_key']
   output_key = valkey_keys['output_key']
   metrics_key = valkey_keys['metrics_key']
   if not key_exists(files_key):
      set_json_data(files_key, [])
   if not key_exists(output_key):
      df = init_frame()
      set_output_frame(output_key, df)
   setup_metrics(metrics_key)

def create_metrics(metrics):
   data = {
      "timeToTranscribePerToken": Metric(**metrics["transcription"]),
      "timeToInference": Metric(**metrics["inference"]),
      "timeToDownload": Metric(**metrics["download"])
   }
   return PerformanceMetrics(**data)

def create_metadata(df):
   event_start = df["start"].min().strftime(DATETIME_FORMAT)
   state_change = df["time_to_change"].values[-1]
   running_clock = pd.Timestamp("now", tz=TIME_ZONE) - df["start"].min()
   running_clock = format_timediff(running_clock.seconds)
   data = {
      "eventStart": event_start,
      "timeToNextEvent": state_change,
      "runningClock": running_clock
   }
   return EventMetaData(**data)

def append_transcriptions(row, transcriptions):
   start = row["start"]
   transcriptions.append(f"{start}: ICOM: {row['track1']}")
   transcriptions.append(f"{start}: TD: {row['track3']}")
   transcriptions.append(f"{start}: CG: {row['track4']}")

def get_transcriptions(df):
   df["start"] = df["start"].dt.strftime(DATETIME_FORMAT)
   transcriptions = []
   df.apply(append_transcriptions, axis=1, transcriptions=transcriptions)
   return transcriptions

def get_state(df):
   current_state = df['state'].values[-1]
   if current_state.startswith("Delay"):
      delay_reason = df["delay type"].values[-1]
      if delay_reason == "":
         return None
      delay_reason = DelayReason(delay_reason)
      resolution = df["time_to_change"].values[-1]
      dly = Delay(**{
         "reason": delay_reason,
         "predictedResolutionTime": resolution
      })
   else:
      dly = None
   return State(**{
      "currentState": CurrentState(current_state),
      "delay": dly
   })

def api_update():
   prefix = get_prefix()
   run_id = get_current_run_id()
   valkeys = get_valkey_keys(prefix, run_id)
   df = get_output_frame(valkeys["output_key"])
   metric_dict = get_json_data(valkeys["metrics_key"])
   metadata = create_metadata(df)
   metrics = create_metrics(metric_dict)
   transcripts = Transcription(**{
      "speechToText": get_transcriptions(df)
   })
   state = get_state(df)
   return Update(**{
      "metadata": metadata,
      "state": state,
      "transcription": transcripts,
      "performanceMetrics": metrics
   })
