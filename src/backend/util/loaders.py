import pandas as pd
import numpy as np
from comms.valkey import get_output_frame, set_output_frame, set_json_data
from comms.valkey import get_hash, set_hash
from comms.valkey import key_exists
from util.logs import get_logger
from util.objects import CurrentState, MetricTracker

log = get_logger()

OUTPUT_COLUMNS = ['start', 'end', 'track1', 'track2',
                  'track3', 'track4', 'state', 'notes', 'delay type']
VALKEY_COLUMNS = OUTPUT_COLUMNS + ['predicted_state', 'seconds_to_state_change']

OUTPUT_STRING_FORMAT = "%-m/%d/Y %I:%M"

def init_frame():
   start_time = pd.Timestamp('now')
   end_time = start_time
   state = CurrentState.pre_trial_start.value
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
      "predicted_state": CurrentState.trial_start.value,
      "seconds_to_state_change": seconds_to_state_change
   }
   return pd.DataFrame([data])

def append_row(frame_key, data):
   row = pd.DataFrame([data])
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
      }
   }
   set_json_data(metric_key, data)

def push_data(data, metrics, valkeys):
   for k, v in data.items():
      push_data = {
         "start":v["start_time"],
         "end":v["end_time"],
         "track1": v.get("track1", ""),
         "track2": v.get("track2", ""),
         "track3": v.get("track3", ""),
         "track4": v.get("track4", ""),
         "state": v["state"],
         "notes": "",
         "delay type": data.get("delay_type", ""),
         "predicted_state": data["predicted_state"],
         "time_to_change": data["time_to_change"]
      }
      append_row(valkeys['output_key'], push_data)
   push_metrics(metrics, valkeys["metrics_key"])

def test_update(run_id):
   to_push = {}
   for i in range(3):
      push


def format_timediff(seconds):
   fmt_seconds = seconds % 60
   minutes = seconds // 60
   fmt_minutes = minutes % 60
   hours = minutes // 60
   return "{:02d}:{:02d}:{:02d}".format(hours,fmt_minutes,fmt_seconds)

def init_outputs(valkey_keys, prefix):
   files_key = valkey_keys['files_key']
   output_key = valkey_keys['output_key']
   if not key_exists(files_key):
      set_json_data(files_key, [])
   if not key_exists(output_key):
      df = init_frame()
      set_output_frame(output_key, df)

def api_update(run_id):
   prefix = get_hash('run_to_prefix')
