# gateway/main.py

from dotenv import load_dotenv
load_dotenv()  # Load environment variables before anything else

import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from gateway.morpheus_controller import MorpheusController, ChatState

app = FastAPI(title="DRMZ Morpheus Gateway")
controller = MorpheusController()

# In-memory session store (swap for persistent DB later if needed)
user_sessions = {}

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_id = body.get("user_id", "anon")
    message = body.get("message", "").strip()

    if not message:
        return JSONResponse(content={"error": "Empty message received."}, status_code=400)

    # Load or initialize session
    state = user_sessions.get(user_id, ChatState())
    state.message = message

    # Process message (sync call)
    updated_state = controller.process_message(state)

    # Save updated state
    user_sessions[user_id] = updated_state

    return JSONResponse({
        "reply": updated_state.response,
        "stage": updated_state.user_data.stage,
        "name": updated_state.user_data.name,
        "captured": updated_state.captured_data
    })
