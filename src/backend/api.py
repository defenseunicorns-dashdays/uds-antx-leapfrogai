from fastapi import FastAPI
from util.objects import Update
from util.loaders import init_frame, test_update
from comms.valkey import set_hash

app = FastAPI()

@app.get("/start/", status_code=201)
async def start() -> int:

   return 1

@app.get("/end/", status_code=200)
async def end() -> Update:
   return Update()

@app.get("/update/", status_code=200)
async def update(run_id: int) -> Update:
   if not run_id:
      run_id = 1
   return test_update(run_id)
