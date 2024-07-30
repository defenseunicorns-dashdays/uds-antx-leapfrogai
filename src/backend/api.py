from fastapi import FastAPI, HTTPException
from util.objects import Update, Run, Transcription
from util.loaders import get_status, get_prefix, get_valkey_keys, init_outputs
from util.loaders import get_current_run, get_output_frame, create_metadata, build_date_response
from util.loaders import create_metrics, get_transcriptions, get_state, parse_date
from comms.valkey import publish_message, get_json_data
import os
import traceback
import logging

tags = [
   {
      "name": "start",
      "description": "date (optional) query param is a MMDDYYYY formatted string to look for audio files.  If None, will use current date"
   }
]

app = FastAPI(openapi_tags=tags)

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] | %(message)s')
log = logging.getLogger()

@app.get("/start/", status_code=201, tags=["start"])
async def start(date:str | None = None) -> Run:
   if date:
      try:
         dt = parse_date(date)
         return init_run(dt)
      except Exception as e:
         log.warning(f"Error parsing date: {date}")
         log.warning(traceback.format_exc())
         raise HTTPException(status_code=400, detail="date query param must be MMDDYYYY format")
   return init_run(None)

@app.get("/end/", status_code=200)
async def end() -> Update:
   end_run()
   return api_update()

@app.get("/update/", status_code=200)
async def update() -> Update:
   return api_update()

def init_run(date):
   prefix, run_id, status = get_status()
   if status == "Running":
      raise HTTPException(status_code=409, detail="Ingestion process is already running!")
   prefix = get_prefix(date)
   run_id += 1
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
   date = build_date_response(date)
   return Run(**{"date":date, "runID":run_id})

def api_update():
   prefix, run_id, status = get_current_run()
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

def end_run():
   prefix, run_id, status = get_status()
   if status != "Running":
      raise HTTPException(status_code=400, detail="No running processes found")
   msg = {
      "message_type": "end",
      "bucket": os.environ.get("READ_BUCKET", "antx"),
      "prefix": prefix,
      "run_id": run_id
   }
   publish_message("events", msg)
