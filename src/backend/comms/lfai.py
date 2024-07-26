import requests
import random
import time
import os
import time as time
import json
import subprocess
import tempfile
from util.logs import get_logger
from util.objects import CurrentState, DelayReason
from util.loaders import format_timediff, get_random_string

log = get_logger()

URL_TRANSCRIPTION = 'https://leapfrogai-api.uds.dev/openai/v1/audio/transcriptions'
URL_INFERENCE = 'https://leapfrogai-api.uds.dev/openai/v1/chat/completions'

# need to decide on the naming convention for the API key
LEAPFROG_API_KEY = os.environ.get('LEAPFROG_API_KEY', 'test')
if not LEAPFROG_API_KEY:
   log.error("LEAPFROG_API_KEY environment variable is not set")
   raise ValueError("LEAPFROG_API_KEY environment variable is not set")

STATE_CHANGE_PROB = .01

def dummy_transcribe(file_path):
   t1 = time.time()
   length = random.randint(20, 30)
   res = get_random_string(length)
   time.sleep(random.randint(4,7))
   t2 = time.time()
   result = {
      "transcription": res,
      "performanceMetrics": {
         "timeToTranscribe": t2 - t1,
         "tokens": random.randint(10,20)
      }
   }
   return json.dumps(result)

def dummy_inference(current_state, data):
   t1 = time.time()
   seconds_to_next_event = random.randint(0, 120)
   formatted_time_to_change = format_timediff(seconds_to_next_event)
   if random.random() < STATE_CHANGE_PROB:
      current_state = random.choice(list(CurrentState)).value
   data['state'] = current_state
   if current_state == 'Delay Start':
      data['delay_type'] = random.choice(list(DelayReason)).value
      data['delay_resolution'] = formatted_time_to_change
   else:
      data["delay_type"] = ""
   data["time_to_change"] = formatted_time_to_change
   time.sleep(random.randint(1, 5))
   data['inference_seconds'] = time.time() - t1
   return data  

def build_transcribe_request(file_path, response_type='json', segmentation=[], logging=False):
   # Check if the file exists
   if not os.path.exists(file_path):
      log.error(f"Error: File '{file_path}' does not exist.")
      return ""

   # Use ffprobe to get detailed information about the file
   command = f'ffprobe -v quiet -print_format json -show_format -show_streams "{file_path}"'
   result = subprocess.run(command, capture_output=True, text=True, shell=True)

   if result.returncode != 0:
      log.error(f"Error running ffprobe: {result.stderr}")
      return ""

   try:
      probe_data = json.loads(result.stdout)
      
      # Check if there are any streams in the file
      if 'streams' not in probe_data or not probe_data['streams']:
         log.info(f"No streams found in {file_path}")
         return ""

      # Look for an audio stream
      audio_streams = [stream for stream in probe_data['streams'] if stream['codec_type'] == 'audio']
      
      if not audio_streams:
         log.info(f"No audio streams found in {file_path}")
         return ""

      if logging:
         log.info(f"Audio stream found in {file_path}")
         log.info(f"Audio codec: {audio_streams[0].get('codec_name', 'Unknown')}")
         log.info(f"Sample rate: {audio_streams[0].get('sample_rate', 'Unknown')} Hz")
         log.info(f"Channels: {audio_streams[0].get('channels', 'Unknown')}")

   except json.JSONDecodeError:
      log.error(f"Error parsing ffprobe output for {file_path}")
      return ""

   # Split audio based on silence or provided segmentation
   if not segmentation:
      split_command = f'ffmpeg -i "{file_path}" -af silencedetect=noise=-30dB:d=0.5 -f null - 2>&1'
      output = subprocess.run(split_command, capture_output=True, text=True, shell=True).stderr

      # Parse silence detection output
      silence_ends = []
      silence_starts = []
      for line in output.split('\n'):
         if 'silence_end' in line:
               silence_ends.append(float(line.split('silence_end: ')[1].split(' ')[0]))
         elif 'silence_start' in line:
               silence_starts.append(float(line.split('silence_start: ')[1].split(' ')[0]))

      # Create chunks
      chunks = []
      if silence_starts and silence_ends:
         chunks.append((0, silence_starts[0]))
         for i in range(len(silence_ends) - 1):
               chunks.append((silence_ends[i], silence_starts[i + 1]))
         chunks.append((silence_ends[-1], None))  # Until the end of the file
      else:
         chunks.append((0, None))  # Whole file if no silence detected
   else:
      chunks = segmentation

   transcriptions = []
   times = []
   tokens = 0

   with tempfile.TemporaryDirectory() as temp_dir:
      for i, (start, end) in enumerate(chunks):
         chunk_path = os.path.join(temp_dir, f'chunk_{i}.mp3')
         if end:
               command = f'ffmpeg -v quiet "{file_path}" -ss {start} -to {end} "{chunk_path}" -y'
         else:
               command = f'ffmpeg -v quiet -i "{file_path}" -ss {start} "{chunk_path}" -y'
         subprocess.run(command, shell=True, check=True)
         
         transcription, time_taken = transcribe_audio(chunk_path)
         tokens += transcription.split(' ')
         transcriptions.append(transcription)
         times.append(time_taken)

   # Calculate performance metrics  
   performance_metrics = {
      "timeToTranscribe": sum(times),
      "tokens": tokens
   }

   result = {
      "transcription": transcriptions,
      "performanceMetrics": performance_metrics
   }

   if response_type == 'json':
      return json.dumps(result)
   else:
      return ' '.join(transcriptions)

def transcribe_audio(file_path):
   url_transcription = URL_TRANSCRIPTION
   headers = {
      'accept': 'application/json',
      'Authorization': f'Bearer {LEAPFROG_API_KEY}'
   }

   with open(file_path, 'rb') as audio_file:
      files = {
         'file': (file_path, audio_file, 'audio/mpeg')
      }

      data = {
         'model': 'whisper',
         'file': f'@{file_path}',
         'language': '',
         'prompt': '',
         'response_format': '',
         'temperature': '1'
      }

      start_time = time.time()
      response = requests.post(url_transcription, headers=headers, files=files, data=data)
      end_time = time.time()

   if response.status_code == 200:
      transcription = response.json()['text']
      time_taken = end_time - start_time
      return transcription, time_taken
   else:
      log.error(f"Error transcribing {file_path}: {response.status_code}")
      return "", 0

def inference(transcription, current_state):
   return dummy_inference(current_state)

