from fastapi import FastAPI, Depends
from util.objects import Update, LastUpdate
from util.loaders import init_frame

app = FastAPI()

@app.get("/start/", status_code=201)
async def start() -> int:
   return 1

@app.get("/end/", status_code=200)
async def end() -> Update:
   return Update()

@app.get("/update/", status_code=200)
async def update(run_id: int, last_state: str) -> Update:
   return Update()