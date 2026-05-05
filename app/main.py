import os
import time # to get currect time
import random #needed for error rate
from pydantic import BaseModel #used by FastAPI to detemine what shape the incoming JSON shouldbe
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Response #HTTPSException let you return error 500
import asyncio #let you do sync sleep ibetter than time.sleep in FatsAPI

app = FastAPI()

START_TIME = time.time() #when the app starts
MODE = os.getenv("MODE", "stable")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

class ChaosRequest(BaseModel):
    mode: str
    duration: int = 0
    rate: float = 0.0

chaos_state = {"mode": None, "duration": 0, "rate": 0.0} #a dictionary that store the current active chaos mode



@app.get("/")
async def root(response: Response):
    if MODE == "canary":
        response.headers["X-Mode"] = "canary"
    if chaos_state["mode"] == "slow":
        await asyncio.sleep(chaos_state["duration"])

    if chaos_state["mode"] == "error":
        if random.random() < chaos_state["rate"]: #random.random generate a random numberr between 0 and 1
            raise HTTPException(status_code=500, detail="chaos error triggered")
        
    return {
        "message": "Welcome to SwiftDeploy",    
        "mode": MODE,
        "version": APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
        }


@app.get("/healthz")
async def healthz():
    uptime = time.time() - START_TIME
    return {
        "status": "ok",
        "uptime": round(uptime, 2)
        }

@app.post("/chaos")
async def chaos(request: ChaosRequest):
    if MODE != "canary": # only work in canary mode
        return {"error": "chaos is only  available in canary mode"}

    #update the chaos state
    chaos_state["mode"] = request.mode
    chaos_state["duration"] = request.duration
    chaos_state["rate"] = request.rate

    if request.mode == "recover":
        chaos_state["mode"] = None
        chaos_state["duration"] = 0
        chaos_state["rate"] = 0.0
        return {"status": "Recovered, back to normal"}
    
    return {"status": f"chaos mode is set to {request.mode}"} #f allows you to put variable inside a string instead of using concatination
