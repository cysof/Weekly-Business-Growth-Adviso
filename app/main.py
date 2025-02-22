import requests
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.config import settings

from app.routers.intergration_config import router as integration_router
from app.routers.insights import router as insights_router
from app.services import generate_insight
from app.models import TickPayload

app = FastAPI(title="Weekly-Business-Growth-Advisor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(insights_router)
app.include_router(integration_router)

logger = logging.getLogger(__name__)

# Constants
TELEX_RETURN_URL = settings.TELEX_WEBHOOK_URL

# Functions
def process_tick_task(payload: TickPayload):
    try:
        insight = generate_insight()
        logger.info(f"Generated insight for {insight.metric}: {insight.observation}")
        
        result_payload = {
            "message": f" {insight.observation}\n {insight.recommendation}",
            "username": "Weekly Business Growth Advisor",
            "event_name": "Weekly Business Insight",
            "status": "success"
        }
        
        response = requests.post(TELEX_RETURN_URL, json=result_payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Successfully posted insight to Telex. Status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Error posting insight to Telex: {e}")

@app.post("/tick", status_code=202)
def tick_endpoint(payload: TickPayload, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_tick_task, payload)
    return {"status": "accepted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)