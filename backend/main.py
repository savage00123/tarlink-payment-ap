import re
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

app = FastAPI(
    title="Starlink Voucher Management Gateway",
    description="Processes manual verification inputs via EcoCash tokens for Zimbabwe reseller fulfillment",
    version="1.0.0"
)

# Configure CORS so your frontend can communicate securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Swap out with your production domain when ready
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Structured data template
class EcoCashPaymentSubmit(BaseModel):
    phone: str = Field(..., description="The subscriber's EcoCash phone number", min_length=9, max_length=15, examples=["771234567"])
    location: str = Field(..., description="The geographical delivery region/province selected", examples=["Harare"])
    planId: str = Field(..., description="Identifier matching selected package price metric", examples=["advanced"])
    agent: str = Field(..., description="Fulfillment agent structural channel name", examples=["Afrilink Data Systems"])
    paymentCodeString: str = Field(..., description="The absolute pasted text string of the confirmation SMS block")

    @field_validator('phone')
    @classmethod
    def clean_phone_number(cls, v: str) -> str:
        # Automatically strip spaces, dashes, or formatting characters
        cleaned = re.sub(r'[\s\-]', '', v)
        if not cleaned.isdigit():
            raise ValueError('Phone number must contain only digits')
        return cleaned

@app.post("/api/ecocash/verify", status_code=status.HTTP_200_OK)
async def process_payment_verification(payload: EcoCashPaymentSubmit):
    """
    Receives phone number, route configuration parameters, and the pasted raw
    EcoCash message token string to complete bundle distribution.
    """
    raw_message = payload.paymentCodeString.strip()
    
    # Structural check: Ensure the message is long enough to be an EcoCash statement
    if len(raw_message) < 25:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The verification message text is too short to be a valid EcoCash SMS confirmation."
        )

    # Automated Token / Txn ID Parsing
    # Looks for a common 10-digit alphanumeric structure unique to transactional texts
    txn_match = re.search(r'\b[A-Z0-9]{10}\b', raw_message)
    txn_id = txn_match.group(0) if txn_match else "NOT_FOUND"

    # Terminal Log for Verification
    print("\n" + "="*50)
    print("📥 NEW STARLINK PAYMENT VERIFICATION REQUEST RECEIVED")
    print(f"📱 EcoCash Phone No: +263 {payload.phone}")
    print(f"🆔 Parsed Txn ID   : {txn_id}")
    print(f"📍 Target Location : {payload.location}")
    print(f"📦 Selected Plan ID: {payload.planId}")
    print(f"💼 Assigned Agent  : {payload.agent}")
    print("-"*50)
    print("📝 RAW MESSAGE PREVIEW:")
    print(raw_message[:120] + "..." if len(raw_message) > 120 else raw_message)
    print("="*50 + "\n")

    return {
        "status": "success",
        "message": "Transaction token profile accepted and parsed successfully.",
        "received_data": {
            "phone_tail": payload.phone[-4:],
            "agent_routed": payload.agent,
            "parsed_txn_id": txn_id,
            "message_length": len(raw_message)
        }
    }

@app.get("/")
def read_root():
    return {"status": "online", "service": "Starlink Zimbabwe Reseller Gateway API Node"}