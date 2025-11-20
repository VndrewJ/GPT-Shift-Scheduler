from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse
import os
from dotenv import load_dotenv
import uvicorn
import requests
from openai import OpenAI
import json

load_dotenv()

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
API_TOKEN = os.getenv("API_TOKEN")
FB_MESSAGER_API_URL = "https://graph.facebook.com/v24.0/me/messages"


# Initial verification endpoint (Required)
@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        # MUST return challenge as plain text, not JSON
        return PlainTextResponse(challenge, status_code=200)

    return PlainTextResponse("Verification failed", status_code=403)


# Receive messages endpoint
@app.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    print("Incoming webhook:", data)

    # Process message in background to avoid Facebook retries
    background_tasks.add_task(process_message, data)
    
    # Return 200 immediately so Facebook doesn't retry
    return {"status": "ok"}


# Process the message in the background
def process_message(data: dict):
    try:
        # Extract Sender ID and message text
        message_payload = data["entry"][0]["messaging"][0]
        if "message" in message_payload and "text" in message_payload["message"]:
            sender_id = message_payload["sender"]["id"]
            message_text = message_payload["message"]["text"]

            # Process message with OpenAI
            response_text = parse_message(message_text)

            # Build a reply string
            reply_text = f"Got it! You requested:\nDay: {response_text.get('day')}\n" \
                         f"Start: {response_text.get('start_time')}\nEnd: {response_text.get('end_time')}"

            send_message(sender_id, reply_text)

    except KeyError:
        print("No message payload found in the request.")
    except Exception as e:
        print(f"Error processing message: {e}")

# Send message to OpenAI
def parse_message(user_message: str) -> dict:
    instructions = """
    You are an assistant that extracts work schedule requests from natural language messages.
    Always respond with JSON in the following format:

    {
    "day": "<Day of the week>",
    "start_time": "<HH:MM 12-hour format>",
    "end_time": "<HH:MM 12-hour format>"
    }

    If any information is missing, return null for that field.
    """
    response = client.responses.create(
        model="gpt-4o",
        instructions=instructions,
        input=user_message,
        temperature=0  # Set as 0 so output is structured and consistent
    )

    output_text = response.output_text.strip()
    try:
        parsed = json.loads(output_text)
    except json.JSONDecodeError:
        parsed = {"day": None, "start_time": None, "end_time": None}

    return parsed
 

# Send message back to user
def send_message(recipient_id: str, message_text: str):
    headers = {"Content-Type": "application/json"}

    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }

    params = {
        "access_token": API_TOKEN
    }

    response = requests.post(FB_MESSAGER_API_URL, params=params, json=payload, headers=headers)
    if response.status_code != 200:
        print("Failed to send message:", response.text)

if __name__ == "__main__":
    port = 8000
    uvicorn.run(app, host="0.0.0.0", port=port)
