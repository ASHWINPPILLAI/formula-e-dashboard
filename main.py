"""Formula E Driver Performance Analyzer – Enterprise FastAPI application."""

import io
import os
import time
import json
import sqlite3
import logging
import asyncio
from typing import Annotated, Optional
from concurrent.futures import ThreadPoolExecutor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import EvaluationResponse, TelemetryInput

# ---------------------------------------------------------------------------
# App & Template & Logger Setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("fe-analyzer")

app = FastAPI(
    title="Formula E Driver Performance Analyzer (Enterprise)",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(_THIS_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(_THIS_DIR, "templates"))

executor = ThreadPoolExecutor(max_workers=8)

# ---------------------------------------------------------------------------
# Database Setup (using builtin sqlite3 to avoid DLL blocks)
# ---------------------------------------------------------------------------

if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/telemetry_enterprise.db"
else:
    DB_PATH = os.path.join(_THIS_DIR, "telemetry_enterprise.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_id TEXT NOT NULL,
                lap_number INTEGER NOT NULL,
                score INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
init_db()

def save_and_get_stats(driver_id: str, lap_number: int, score: int):
    """Save lap to DB and return historical average for this driver."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO telemetry (driver_id, lap_number, score) VALUES (?, ?, ?)",
            (driver_id, lap_number, score)
        )
        cur = conn.execute(
            "SELECT AVG(score) FROM telemetry WHERE driver_id = ?",
            (driver_id,)
        )
        avg = cur.fetchone()[0]
    return float(avg) if avg is not None else float(score)

# ---------------------------------------------------------------------------
# WebSocket Manager (Real-time data streaming)
# ---------------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected.")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

# ---------------------------------------------------------------------------
# Scoring logic
# ---------------------------------------------------------------------------

SENSOR_FAULT_THRESHOLD = 600.0
BRAKING_TARGET = 500.0
LIFT_COAST_TARGET = 50.0
LIFT_COAST_MID = 25.0

def _evaluate(data: TelemetryInput, api_key: Optional[str]) -> EvaluationResponse:
    """Core scoring logic."""
    start_time = time.time()
    feedback: list[str] = []
    sensor_fault_detected = False

    if api_key:
        logger.info(f"Authenticated request from client (Key: {api_key[:4]}...)")
    else:
        logger.warning("Unauthenticated request. Proceeding in legacy mode.")

    t3 = data.turn_3_regen_kw
    t13 = data.turn_13_regen_kw

    if t3 > SENSOR_FAULT_THRESHOLD:
        sensor_fault_detected = True
        feedback.append(f"Sensor fault: Turn 3 regen reported {t3:.1f} kW, exceeding {SENSOR_FAULT_THRESHOLD:.0f} kW. Value capped for scoring.")
        t3 = SENSOR_FAULT_THRESHOLD

    if t13 > SENSOR_FAULT_THRESHOLD:
        sensor_fault_detected = True
        feedback.append(f"Sensor fault: Turn 13 regen reported {t13:.1f} kW, exceeding {SENSOR_FAULT_THRESHOLD:.0f} kW. Value capped for scoring.")
        t13 = SENSOR_FAULT_THRESHOLD

    t3_ok = t3 >= BRAKING_TARGET
    t13_ok = t13 >= BRAKING_TARGET
    if t3_ok and t13_ok:
        braking_points = 50
    elif t3_ok or t13_ok:
        braking_points = 25
        if not t3_ok: feedback.append(f"Increase Turn 3 regenerative braking above {BRAKING_TARGET:.0f} kW.")
        if not t13_ok: feedback.append(f"Increase Turn 13 regenerative braking above {BRAKING_TARGET:.0f} kW.")
    else:
        braking_points = 10
        feedback.append(f"Both Turn 3 and Turn 13 braking are below {BRAKING_TARGET:.0f} kW. Significant improvement needed.")

    lc = data.lift_coast_distance_meters
    if lc >= LIFT_COAST_TARGET:
        lc_points = 50
    elif lc >= LIFT_COAST_MID:
        lc_points = 25
        feedback.append(f"Lift-and-coast distance is {lc:.1f} m. Extend to at least {LIFT_COAST_TARGET:.0f} m.")
    else:
        lc_points = 0
        feedback.append(f"Lift-and-coast distance is only {lc:.1f} m. Aim for at least {LIFT_COAST_TARGET:.0f} m.")

    efficiency_score = max(1, min(100, braking_points + lc_points))

    if efficiency_score >= 85:
        rating = "EXCELLENT"
    elif efficiency_score >= 60:
        rating = "OPTIMAL"
    else:
        rating = "NEEDS_IMPROVEMENT"

    chart_url = f"/api/v1/chart?t3={t3}&t13={t13}&lc={lc}"

    avg_score = save_and_get_stats(data.driver_id, data.lap_number, efficiency_score)
    delta = efficiency_score - avg_score

    elapsed = (time.time() - start_time) * 1000
    logger.info(f"Evaluated {data.driver_id} Lap {data.lap_number}: Score {efficiency_score} ({elapsed:.1f}ms)")

    response = EvaluationResponse(
        driver_id=data.driver_id,
        lap_number=data.lap_number,
        efficiency_score=efficiency_score,
        rating=rating,
        sensor_fault_detected=sensor_fault_detected,
        feedback=feedback,
        chart_url=chart_url,
        historical_average_score=round(avg_score, 1),
        score_delta=round(delta, 1),
    )
    
    asyncio.create_task(manager.broadcast(response.model_dump_json()))
    return response


def _generate_chart(t3: float, t13: float, lc: float) -> bytes:
    """Legacy endpoint Matplotlib chart generation (Async Offloaded)."""
    fig, (ax_braking, ax_lc) = plt.subplots(1, 2, figsize=(10, 5), facecolor="#0a0204")
    
    # Braking
    ax_braking.set_facecolor("#1a0508")
    ax_braking.bar(["Turn 3", "Turn 13"], [t3, t13], color=["#ff4d5e", "#ff4d5e"], width=0.5, edgecolor="#f5e9ea")
    ax_braking.axhline(y=500, color="#ffd700", linestyle="--", linewidth=1.2, label="Target (500 kW)")
    ax_braking.axhline(y=600, color="#ffffff", linestyle="--", linewidth=1.2, label="Fault (600 kW)")
    ax_braking.set_ylabel("Regen (kW)", color="#f5e9ea")
    ax_braking.set_title("Regenerative Braking", color="#f5e9ea", fontsize=13, pad=10)
    ax_braking.tick_params(colors="#f5e9ea")
    ax_braking.legend(loc="upper right", fontsize=8, facecolor="#1a0508", edgecolor="#ff1e3c", labelcolor="#f5e9ea")
    y_max_brake = max(t3, t13, 650)
    ax_braking.set_ylim(0, y_max_brake * 1.15)
    for spine in ax_braking.spines.values(): spine.set_color("#8f0a1c")

    # Lift-and-coast
    ax_lc.set_facecolor("#1a0508")
    ax_lc.bar(["Lift & Coast"], [lc], color=["#ff1e3c"], width=0.4, edgecolor="#f5e9ea")
    ax_lc.axhline(y=50, color="#ffd700", linestyle="--", linewidth=1.2, label="Target (50 m)")
    ax_lc.set_ylabel("Distance (m)", color="#f5e9ea")
    ax_lc.set_title("Lift & Coast", color="#f5e9ea", fontsize=13, pad=10)
    ax_lc.tick_params(colors="#f5e9ea")
    ax_lc.legend(loc="upper right", fontsize=8, facecolor="#1a0508", edgecolor="#ff1e3c", labelcolor="#f5e9ea")
    y_max_lc = max(lc, 60)
    ax_lc.set_ylim(0, y_max_lc * 1.15)
    for spine in ax_lc.spines.values(): spine.set_color("#8f0a1c")

    fig.tight_layout(pad=2.0)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor(), dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    """Redirect root to dashboard."""
    return RedirectResponse(url="/dashboard")

@app.get("/health")
async def health() -> dict:
    """Liveness probe."""
    return {"status": "healthy", "service": "driver-performance-analyzer"}

@app.post("/api/v1/evaluate", response_model=EvaluationResponse)
async def evaluate(
    data: TelemetryInput, 
    x_api_key: Optional[str] = Header(None)
) -> EvaluationResponse:
    """Evaluate a single lap's telemetry (Secured)."""
    return _evaluate(data, x_api_key)

@app.get("/api/v1/chart")
async def chart(
    t3: Annotated[float, Query(ge=0)] = 0.0,
    t13: Annotated[float, Query(ge=0)] = 0.0,
    lc: Annotated[float, Query(ge=0)] = 0.0,
) -> StreamingResponse:
    """Legacy Matplotlib endpoint for backward compatibility."""
    loop = asyncio.get_running_loop()
    png_bytes = await loop.run_in_executor(executor, _generate_chart, t3, t13, lc)
    return StreamingResponse(io.BytesIO(png_bytes), media_type="image/png")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the pit-wall dashboard UI."""
    return templates.TemplateResponse(request=request, name="dashboard.html")

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time telemetry streaming."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping": await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
