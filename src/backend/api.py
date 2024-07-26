from fastapi import FastAPI
from util.objects import Update
from util.loaders import init_run, api_update, end_run
import logging

app = FastAPI()

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] | %(message)s')

@app.get("/start/", status_code=204)
async def start() -> None:
   init_run()
   return 

@app.get("/end/", status_code=200)
async def end() -> Update:
   end_run()
   return api_update()

@app.get("/update/", status_code=200)
async def update() -> Update:
   return api_update()
