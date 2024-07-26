from fastapi import FastAPI
from util.objects import Update
from util.loaders import init_run, api_update, end_run

app = FastAPI()

@app.get("/start/", status_code=201)
async def start() -> int:
   run_id = init_run()
   return run_id

@app.get("/end/", status_code=200)
async def end(run_id: int) -> Update:
   end_run(run_id)
   return api_update(run_id)

@app.get("/update/", status_code=200)
async def update(run_id: int) -> Update:
   if not run_id:
      raise Exception
   return api_update(run_id)
