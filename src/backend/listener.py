from comms.valkey import wipe_key, get_valkey_connection
from util.logs import get_logger, setup_logging
import os
import json
import traceback
from subprocess import Popen
from util.loaders import get_valkey_keys

log = get_logger()

class Listener:
   def __init__(self):
      self.r = get_valkey_connection()
      self.sub_channel = os.environ.get('SUB_CHANNEL', 'events')
      self.processes = {}

   def spawn_process(self, bucket, key_prefix, run_id):
      cmd = ["python3", "ingest.py", bucket, key_prefix, run_id]
      log.info(f'Creating process with command: {cmd}')
      self.processes[key_prefix] = Popen(cmd)

   def start_ingestion(self, data):
      key_prefix = data['prefix']
      bucket = data['bucket']
      run_id = data['run_id']
      if key_prefix in self.processes:
         log.warning(f'Attempting to start proccess that already exists:')
         proc = self.processes[key_prefix]
         code = proc.poll()
         if code is None:
            log.warning(f'Process is running...')
         else:
            log.warning(f'Process exited with code: {code}, use a resume message to resume')
      else:
         self.spawn_process(bucket, key_prefix, run_id)

   def resume_ingestion(self, data):
      key_prefix = data['prefix']
      bucket = data['bucket']
      run_id = data['run_id']
      if key_prefix not in self.processes:
         log.warning(f'{key_prefix} Not found in processes, use a start message to start')
      else:
         proc = self.processes[key_prefix]
         code = proc.poll()
         if code is None:
            log.warning(f'{key_prefix} Subprocess is still running, use an end message to stop')
         else:
            self.spawn_process(bucket, key_prefix, run_id)
   
   def end_ingestion(self, data):
      key_prefix = data['prefix']
      if key_prefix not in self.processes:
         log.warning(f'{key_prefix} is not associated with a process')
      else:
         proc = self.processes[key_prefix]
         code = proc.poll()
         if code is not None:
            log.warning(f'{key_prefix} Process exited with code {code}. Use a resume message to restart')
         else:
            log.info(f'Killing process associated with key: {key_prefix}')
            proc.kill()
            del self.processes[key_prefix]

   def wipe_data(self, data):
      key_prefix = data['prefix']
      redis_keys = get_valkey_keys(key_prefix)
      for k, v in redis_keys.items():
         wipe_key(v)

   def process_message(self, data):
      data = json.loads(data)
      msg_type = data['message_type']
      if msg_type == 'start':
         self.start_ingestion(data)
      elif msg_type == 'resume':
         self.resume_ingestion(data)
      elif msg_type == 'end':
         self.end_ingestion(data)
      elif msg_type == 'error':
         self.wait_and_resume(data)
      elif msg_type == 'wipe':
         self.wipe_data(data)
      else:
         log.warn(f'Could not process message: {data}')

   def run(self):
      r = self.r
      pubsub = r.pubsub()
      pubsub.subscribe(self.sub_channel)
      log.info(f'Subscribed to {self.sub_channel}, listening for messages')
      for message in pubsub.listen():
         if message['type'] == 'message':
            log.info(f"Recieved message: {message['data'].decode('utf-8')}")
            try:
               self.process_message(message['data'])
            except Exception as e:
               log.warning(f'Error processing message: {message}, {e}')
               log.warning(traceback.format_exc())
         else:
            log.info(f'Non-message received: {message}')

if __name__ == '__main__':
   setup_logging()
   listener = Listener()
   listener.run()
