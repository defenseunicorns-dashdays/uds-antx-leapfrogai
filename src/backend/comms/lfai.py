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
from prompts.system_prompt_quotes_v3 import sys_prompt
from enums.tracks import track_mapping
from prompts.state_options import next_state_options
from prompts.user_prompt_quotes_v3 import user, examples
from typing import Any

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
   trans = []
   for i in range (4):
      res = get_random_string(length)
      #time.sleep(random.randint(4,7))
      trans.append(res)
   t2 = time.time()
   result = {
      "transcription": res,
      "performanceMetrics": {
         "timeToTranscribe": t2 - t1,
         "tokens": random.randint(10,20)
      }
   }
   return result

def dummy_inference(data):
   t1 = time.time()
   seconds_to_next_event = random.randint(0, 120)
   formatted_time_to_change = format_timediff(seconds_to_next_event)
   current_state = data['state']
   if random.random() < STATE_CHANGE_PROB:
      current_state = random.choice(list(CurrentState)).value
   data['state'] = current_state
   if current_state.startswith('Delay'):
      data['delay_type'] = random.choice(list(DelayReason)).value
      data['delay_resolution'] = formatted_time_to_change
   else:
      data["delay_type"] = ""
   data["time_to_change"] = formatted_time_to_change
   #time.sleep(random.randint(1, 5))
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
      "timeToTranscribe": sum(times) ,
      "tokens": tokens    
   }

   result = {
      "transcription": transcriptions,
      "performanceMetrics": performance_metrics
   }

   if response_type == 'json':
      return result
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

def inference(data_dict):
   return dummy_inference(data_dict)

def parse_data_object(data_object: dict[str,Any]) -> str:
    '''
    Given a data object representing a single minute of radio tracks,
    this function parses the tracks, maps the original track names to 
    their functional names, and joins them with a double new-line break.
    '''
    tracks = [{k:v} for k,v in data_object.items() if k.startswith('track')]
    mapped_tracks = []
    for track in tracks:
        for key, value in track.items():
            mapped_tracks.append(f'{track_mapping[key]}: {value}')
    return '\n\n'.join(mapped_tracks)

def build_user_message(base_user_prompt: str,
                       examples: str, 
                       current_state: str, 
                       radio_tracks: str, 
                       next_state_options_dict: dict
                       ) -> str:
    '''
    Builds user message string variable from dynamic string parameters.
    '''
    next_state_options = next_state_options_dict[current_state]
    user_prompt = base_user_prompt.format(examples=examples, 
                                          current_state=current_state, 
                                          transmissions=radio_tracks, 
                                          next_state_options=next_state_options
                                          )
    return user_prompt


def _format_response(response: requests.models.Response) -> str:
    '''
    Reformats model response from json to a string
    '''
    json_response = response.json()
    return json_response['choices'][0]['message']['content'].strip()

def chat_completion(data_dict: dict,
                    temperature: float=0.8,
                    max_tokens: int=250,
                    stream: bool=False,
                    raw: bool=False
                    ) -> str | dict:
   current_state = data['state']
   tracks = parse_data_object(data_dict)
   user_prompt = build_user_message(user, 
                                 examples, 
                                 current_state, 
                                 tracks, 
                                 next_state_options)
   url = os.environ['LEAPFROG_URL']
   api_key = os.environ['LEAPFROG_API_KEY']
   headers = {
   'Authorization': f'Bearer {api_key}',
   'Content-Type': 'application/json'
   }
   data = {
      "model": "vllm",
      "messages": [
         {
               "role": "system",
               "content": sys_prompt
         },
         {
               "role": "user",
               "content": user_prompt,
         }
      ],
      "stream": stream,
      "temperature": temperature,
      "max_tokens": max_tokens
   }
   try:
      response = requests.post(url, headers=headers, data=json.dumps(data))
      if response.status_code == 200:
         if raw:
               return response.json()
         else: return _format_response(response)
      else:
         print('Response is not 200')
         return response
   except Exception as e:
      print(e)
   # I need the output of this function to be the data_dict with the following changes
      #{
         #start_time: datetime64[ns]
         #end_time: datetime64[ns]
         #track#: string of transcription for that track (multiple tracks)
         #state: string of current state  ### UPDATE THIS
         #delay_type: the type of delay   ### UPDATE THIS
         ##### Appended fields ####
         #time_to_change: string HH:MM until next state change
         #inference_seconds: float - how long the inference took
      #}

   # I can write the function to change the output to this format but I will need an example output
