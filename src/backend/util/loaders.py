import pandas as pd
import numpy as np
import random
import string
from comms.valkey import get_output_frame, set_output_frame, set_json_data
from comms.valkey import get_hash, set_hash, get_json_data
from comms.valkey import key_exists, wipe_key
from util.logs import get_logger
from util.objects import *
log = get_logger()

OUTPUT_COLUMNS = ['start', 'end', 'track1', 'track2',
                  'track3', 'track4', 'state', 'notes', 'delay type']
VALKEY_COLUMNS = OUTPUT_COLUMNS + ['seconds_to_state_change']

OUTPUT_STRING_FORMAT = "%-m/%d/Y %I:%M"

def format_timediff(seconds):
   fmt_seconds = seconds % 60
   minutes = seconds // 60
   fmt_minutes = minutes % 60
   hours = minutes // 60
   return "{:02d}:{:02d}:{:02d}".format(hours,fmt_minutes,fmt_seconds)

def get_random_string(length):
   return random.choices(string.ascii_uppercase + string.digits, k=length)

def get_valkey_keys(prefix, run_id):
   return {
      'files_key': f'{prefix}_processed_files',
      'output_key': f'{run_id}_output',
      'metrics_key': f'{run_id}_metrics'
         }

def wipe_data(key_prefix):
   keys = get_valkey_keys(key_prefix)
   for k, v in keys.items():
      wipe_key(v)

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
      "seconds_to_state_change": seconds_to_state_change
   }
   return pd.DataFrame([data])

def init_run():
   #TODO: track this in valkey
   run_id = -1
   ts = pd.Timestamp("now")
   y = ts.year
   m = ts.month
   d = ts.day
   prefix = "Distribution-Statement-D/{y}/{m}/{d}/"
   wipe_data()

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
         "time_to_change": data["time_to_change"]
      }
      append_row(valkeys['output_key'], push_data)
   push_metrics(metrics, valkeys["metrics_key"])

def test_update(run_id, output_key, metrics_key):
   start_time = pd.Timestamp('now')
   length = random.randint(10, 30)
   change_seconds = int(np.random.normal(120, 45, 1)[0])
   push_data = {
      "start":start_time,
      "end": start_time,
      "track1": get_random_string(length),
      "track2": get_random_string(length),
      "track3": get_random_string(length),
      "track4": get_random_string(length),
      "state": random.choice(list(CurrentState)).value,
      "notes": "",
      "delay_type": "",
      "predicted_state": random.choice(list(CurrentState)).value,
      "time_to_change": format_timediff(change_seconds)
   }
   if push_data["state"] == CurrentState.delay_start:
      push_data["delay_type"] = random.choice(list(DelayReason)).value
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

def init_outputs(valkey_keys, prefix):
   files_key = valkey_keys['files_key']
   output_key = valkey_keys['output_key']
   if not key_exists(files_key):
      set_json_data(files_key, [])
   if not key_exists(output_key):
      df = init_frame()
      set_output_frame(output_key, df)

def create_metrics(metrics):
   data = {
      "timeToTranscribePerToken": Metric(**metrics["transcription"]),
      "timeToInference": Metric(**metrics["inference"])
   }
   return PerformanceMetrics(**data)

def create_metadata(df):
   event_start = df["start_time"].min().strftime(DATETIME_FORMAT)
   state_change = df["time_to_change"].values[-1]
   running_clock = pd.Timestamp("now") - df["start_time"].min()
   running_clock = format_timediff(running_clock.seconds)
   data = {
      "eventStart": event_start,
      "timeToNextEvent": state_change,
      "runningClock": running_clock
   }
   return EventMetaData(data)

def append_transcriptions(row, transcriptions):
   start = row["start"]
   transcriptions.append(f"{start}: ICOM: {row['track1']}")
   transcriptions.append(f"{start}: TD: {row['track3']}")
   transcriptions.append(f"{start}: CG: {row['track4']}")

def get_transcriptions(df):
   df["start"] = df["start"].dt.strftime(DATETIME_FORMAT)
   transcriptions = []
   df.apply(append_transcriptions, axis=1, transcriptions=transcriptions)

def get_state(df):
   current_state = df['state'].values[-1]
   if current_state == CurrentState.delay_start:
      delay_reason = df["delay_type"].values[-1]
      resolution = df["time_to_change"].values[-1]
      dly = Delay({
         "reason": delay_reason,
         "predictedResolutionTime": resolution
      })
   else:
      dly = None
   return State({
      "currentState": CurrentState(current_state),
      "delay": dly
   })

def api_update(run_id):
   prefix = get_hash('run_to_prefix', run_id)
   valkeys = get_valkey_keys(prefix, run_id)
   test_update(run_id, valkeys["output_key"], valkeys["metrics_key"])
   df = get_output_frame(valkeys["output_key"])
   metric_dict = get_json_data(valkeys["metrics_key"])
   metadata = create_metadata(df)
   metrics = create_metrics(metric_dict)
   transcripts = Transcription({
      "speechToText": get_transcriptions(df)
   })
   state = get_state(df)
   return Update({
      "metadata": metadata,
      "state": state,
      "transcription": transcripts,
      "performanceMetrics": metrics
   })
