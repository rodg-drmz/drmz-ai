from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from openai import OpenAI
import os

# Load environment variables
load_dotenv()
client = OpenAI()

# Initialize FastAPI app
app = FastAPI()

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_id = body.get("user_id", "anon")
    message = body.get("message", "")

    # Create a new thread for each user message
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message
    )

    # Run the assistant with streaming
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id="asst_5AyAw1WHxg7eOL847byMYcpr",
        stream=True,
    )

    # Sync generator for SSE streaming
    def event_stream():
        for chunk in run:
            if chunk.event == "thread.message.delta":
                content = chunk.data.delta.content or ""
                if content:
                    yield f"data: {content}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
