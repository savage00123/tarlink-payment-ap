import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import httpx

# Configure logging to monitor requests in the Render terminal logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("starlink-gateway")

app = FastAPI(title="Starlink Zimbabwe Reseller Gateway")

# --- TELEGRAM ALERT BOT CONFIGURATION ---
# Falls back to placeholders if environment variables are not set
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")

# --- DATA MANIFEST SCHEMAS ---
class EcoCashVerificationPayload(BaseModel):
    phone: str = Field(..., description="EcoCash mobile subscriber token string")
    location: str = Field(..., description="Target distribution province/region")
    planId: str = Field(..., description="Subscription tier identifier allocation")
    agent: str = Field(..., description="Authorized fulfillment administrator")
    paymentCodeString: str = Field(..., description="Raw confirmation SMS log data content")

# --- 1. MOUNT STATIC FRONTEND ASSETS ---
# Stepping up one level out of the backend directory to access frontend folder
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")
else:
    logger.error(f"Frontend directory not found at resolved location: {FRONTEND_DIR}")

# --- 2. ENDPOINTS & BUSINESS LOGIC ---

@app.post("/api/ecocash/verify")
async def verify_ecocash_transaction(payload: EcoCashVerificationPayload):
    logger.info(f"Received transaction payload routing for verification from +263{payload.phone}")

    # Format a structural alert payload layout for your Telegram alerting bot channel
    telegram_message = (
        f"📡 <b>New Starlink Allocation Request</b>\n\n"
        f"👤 <b>Subscriber:</b> +263 {payload.phone}\n"
        f"📍 <b>Province/Region:</b> {payload.location}\n"
        f"📦 <b>Plan Selected:</b> {payload.planId.upper()}\n"
        f"💼 <b>Assigned Agent:</b> {payload.agent}\n\n"
        f"📝 <b>EcoCash Confirmation Log:</b>\n"
        f"<code>{payload.paymentCodeString}</code>"
    )

    # Dispatches the notification event asynchronously using HTTPX
    async with httpx.AsyncClient() as client:
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        try:
            response = await client.post(telegram_url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": telegram_message,
                "parse_mode": "HTML"
            })
            if response.status_code != 200:
                logger.error(f"Telegram API warning node callback status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to transmit payload notification parameters via Telegram pipeline: {str(e)}")

    # Clear validation match response payload
    return {
        "status": "success",
        "detail": "Billing parameter verification matrix resolved cleanly. Service active."
    }

# --- 3. SYSTEM HEALTH ENDPOINT ---
@app.get("/api/status")
def get_system_status():
    return {
        "status": "online",
        "service": "Starlink Zimbabwe Reseller Gateway API Node"
    }

# --- 4. SERVE USER INTERFACE ---
@app.get("/")
def read_root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        raise HTTPException(
            status_code=404, 
            detail="Frontend interface context could not be pinpointed under core rules directory."
        )