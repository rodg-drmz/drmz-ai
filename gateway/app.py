from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv
from openai import OpenAI
import os

# ── Load Environment Variables ────────────────────────
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID", "asst_5AyAw1WHxg7eOL847byMYcpr")  # fallback default

if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY not found in .env file.")

# ── Initialize OpenAI Client ───────────────────────────
client = OpenAI(api_key=OPENAI_API_KEY)

# ── FastAPI App Init ───────────────────────────────────
app = FastAPI(title="DRMZ Morpheus Gateway")

# ── Routes ─────────────────────────────────────────────
@app.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        user_id = body.get("user_id", "anon")
        message = body.get("message", "").strip()

        if not message:
            return JSONResponse(content={"error": "Empty message received."}, status_code=400)

        # Create a new thread and add user message
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message
        )

        # Run assistant with streaming response
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID,
            stream=True,
        )

        # ── Streaming Generator ─────────────────────────
        def event_stream():
            for chunk in run:
                if chunk.event == "thread.message.delta":
                    content = getattr(chunk.data.delta, "content", "")
                    if content:
                        yield content

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )
