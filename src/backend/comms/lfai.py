import requests
import random
import string
import time
import os
from util.logs import get_logger
from util.objects import CurrentState, DelayReason
from util.loaders import format_timediff

log = get_logger()

LFAI_KEY = os.environ.get("LFAI_KEY")
STATE_CHANGE_PROB = .01

def dummy_transcribe(file_path):
   t1 = time.time()
   length = random.randint(20, 30)
   res = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
   time.sleep(random.randint(4,7))
   t2 = time.time()
   return res, t2-t1

def dummy_inference(current_state):
   t1 = time.time()
   data = {}
   seconds_to_next_event = random.randint(0, 120)
   formatted_time_to_change = format_timediff(seconds_to_next_event)
   if random.random() < STATE_CHANGE_PROB:
      current_state = random.choice(list(CurrentState)).value
   data['state'] = current_state
   if current_state == 'Delay Start':
      data['delay_reason'] = random.choice(list(DelayReason)).value
      data['delay_resolution'] = formatted_time_to_change
   time.sleep(random.randint(1, 5))
   data['seconds'] = time.time() - t1
   return data

def build_transcribe_request(file_path, response_type='json', segmentation=[]):
   raise NotImplementedError

def transcribe(file_path):
   return dummy_transcribe()

def inference(transcription, current_state):
   return dummy_inference(current_state)
