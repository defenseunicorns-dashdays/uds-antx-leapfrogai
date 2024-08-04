from comms.valkey import get_valkey_connection, set_json_data, STATUS_KEY, key_exists
from util.logs import get_logger, setup_logging
import os
import json
import traceback
from subprocess import Popen
from util.loaders import wipe_data, get_current_run


log = get_logger()

class Listener:
   def __init__(self):
      self.r = get_valkey_connection()
      self.sub_channel = os.environ.get('SUB_CHANNEL', 'events')
      self.process = None
      self.prefix = None
      prefix, run_id, status = get_current_run()
      log.info(f"Initializing with run_id set to {run_id}")
      self.run_id = run_id

   def spawn_process(self, bucket, key_prefix, run_id):
      self.run_id = run_id
      self.prefix = key_prefix
      cmd = ["python3", "ingest.py", bucket, key_prefix, str(self.run_id)]
      log.info(f'Creating process with command: {cmd}')
      self.process = Popen(cmd)
      data = {"prefix": key_prefix, "run_id": run_id, "status":"Running"}
      log.info(f"Setting current process status to {data}")
      set_json_data(STATUS_KEY, data)

   def start_ingestion(self, data):
      key_prefix = data['prefix']
      bucket = data['bucket']
      run_id = data["run_id"]
      if self.process:
         log.warning(f'Attempting to start ingestion while a process exists')
         proc = self.process
         code = proc.poll()
         if code is None:
            log.warning(f'Process is running, not starting')
         else:
            log.warning(f'Process exited with code: {code}')
            self.spawn_process(bucket, key_prefix, run_id)
      else:
         self.spawn_process(bucket, key_prefix, run_id)

   def resume_ingestion(self, data):
      key_prefix = data['prefix']
      bucket = data['bucket']
      run_id = data["run_id"]
      proc = self.process
      if not proc:
         log.warning(f'No process found, use a start message to start')
      else:
         code = proc.poll()
         if code is None:
            log.warning(f'{key_prefix} Subprocess is still running, use an end message to stop')
         else:
            self.spawn_process(bucket, key_prefix, run_id)
   
   def end_ingestion(self, data):
      key_prefix = data['prefix']
      proc = self.process
      if not proc:
         log.warning(f'No running process')
      else:
         code = proc.poll()
         if code is not None:
            log.warning(f'{key_prefix} Process exited with code {code}. Use a resume message to restart')
         else:
            log.info(f'Killing process associated with key: {key_prefix}')
            proc.kill()
            del proc
            self.process = None

   def wait_and_resume(self, data):
      key_prefix = data["prefix"]
      bucket = data["bucket"]
      restart = data["restart"]
      run_id = data["run_id"]
      proc = self.process
      code = proc.wait()
      if restart:
         self.spawn_process(bucket, key_prefix, run_id+1)

   def push_status(self):
      prefix, run_id, status = get_current_run()
      if run_id != self.run_id:
         log.warning(f"RUN_ID MISMATCH IN LISTENER: {self.run_id} listener ID does not match {run_id}")
      proc = self.process
      if not proc:
         status = "Available"
      else:
         code = proc.poll()
         if code is None:
            status = "Running"
         elif code == 0:
            status = "Completed"
         else:
            status = f"Exited with code {code}"
      data = {"run_id": run_id, "prefix": prefix, "status": status}
      set_json_data(STATUS_KEY, data)

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
         wipe_data(data['prefix'], data['run_id'])
      elif msg_type == "status":
         self.push_status()
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
