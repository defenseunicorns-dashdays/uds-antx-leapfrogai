import requests
import random
import string
import time
import os
from util.logs import get_logger
from util.objects import CurrentState, DelayReason

log = get_logger()

LFAI_KEY = os.environ.get("LFAI_KEY")
STATE_CHANGE_PROB = .01

def format_timediff(seconds):
   fmt_seconds = seconds % 60
   minutes = seconds // 60
   fmt_minutes = minutes % 60
   hours = minutes // 60
   print(hours, fmt_minutes, fmt_seconds)
   return "{:02d}:{:02d}:{:02d}".format(hours,fmt_minutes,fmt_seconds)

def dummy_transcribe(file_path):
   t1 = time.time()
   length = random.randint(20, 30)
   res = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
   t2 = time.time()
   return res, t2-t1

def dummy_inference(current_state):
   data = {}
   seconds_to_next_event = random.randint(0, 120)
   formatted_time_to_change = format_timediff(seconds_to_next_event)
   if random.random() < STATE_CHANGE_PROB:
      current_state = random.choice(list(CurrentState)).value
   data['state'] = current_state
   if current_state == 'Delay Start':
      data['delay_reason'] = random.choice(list(DelayReason)).value
      data['delay_resolution'] = formatted_time_to_change

def build_transcribe_request(file_path, response_type='json', segmentation=[]):
   raise NotImplementedError

def transcribe(file_path):
   return dummy_transcribe()

def inference(transcription, current_state):
   return dummy_inference(current_state)
