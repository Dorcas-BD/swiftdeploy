import os
import time # to get currect time
import random #needed for error rate
from pydantic import BaseModel #used by FastAPI to detemine what shape the incoming JSON shouldbe
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Response #HTTPSException let you return error 500
import asyncio #let you do sync sleep ibetter than time.sleep in FatsAPI
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge

app = FastAPI()

#custom metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"]
)

#histogram tracks how long it takes and group them into buckets
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

#gauge tracks a value thats goes up and down like temperature, uptime, mode and chaos state
app_uptime_seconds = Gauge("app_uptime_seconds", "App uptime in seconds")
app_mode_gauge = Gauge("app_mode", "App mode 0=stable 1=canary")
chaos_active = Gauge("chaos_active", "Chaos state is 0=none 1=slow 2=error")

Instrumentator().instrument(app).expose(app) #track all request, latency and status code and expose /metrics

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
    start = time.time()

    if MODE == "canary":
        response.headers["X-Mode"] = "canary"
        app_mode_gauge.set(1)
    else:
        app_mode_gauge.set(0)

    if chaos_state["mode"] == "slow":
        await asyncio.sleep(chaos_state["duration"])

    if chaos_state["mode"] == "error":
        if random.random() < chaos_state["rate"]: #random.random generate a random numberr between 0 and 1
            http_requests_total.labels(method="GET", path="/", status_code="500").inc()
            http_request_duration_seconds.observe(time.time() - start)
            raise HTTPException(status_code=500, detail="chaos error triggered")

    http_requests_total.labels(method="GET", path="/", status_code="200").inc()
    http_request_duration_seconds.observe(time.time() - start)
    app_uptime_seconds.set(time.time() - START_TIME)

    return {
        "message": "Welcome to SwiftDeploy",    
        "mode": MODE,
        "version": APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
        }


@app.get("/healthz")
async def healthz():
    uptime = time.time() - START_TIME
    app_uptime_seconds.set(uptime)
    http_requests_total.labels(method="GET", path="/healthz", status_code="200").inc()
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
        chaos_active.set(0)
        return {"status": "Recovered, back to normal"}
    if request.mode == "slow":
        chaos_active.set(1)
    elif request.mode == "error":
        chaos_active.set(2)

    return {"status": f"chaos mode is set to {request.mode}"} #f allows you to put variable inside a string instead of using concatination
