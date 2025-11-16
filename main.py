from fastapi import FastAPI, Request
import os
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_verify_token")


# 1️⃣ Verification endpoint (Facebook calls this once)
@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)   # MUST return challenge
    return {"error": "Verification failed"}


# 2️⃣ Messenger sends messages here
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("📩 Incoming webhook:", data)
    return {"status": "ok"}  # Always respond 200


if __name__ == "__main__":
    port = 8000
    print(f"🚀 Starting FastAPI server on port {port}")
    print(f"📋 Webhook endpoint: http://localhost:{port}/webhook")
    
    # Run FastAPI app
    uvicorn.run(app, host="0.0.0.0", port=port)
