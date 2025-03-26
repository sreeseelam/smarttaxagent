import os
from datetime import datetime, timedelta
from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
from fastapi.staticfiles import StaticFiles

import httpx
import tiktoken


# Constants
ASSISTANT_ID = "asst_7EMMJF5uOdbyVxHUm82jFAiJ"
FILE_ID = "file-SukV5QChXad2mVPo3CL5Cq"
SYSTEM_PROMPT = "You are a smart, highly accurate, precise and concise Income Tax Assistant to optimize tax returns for maximum refund and prepare Tax returns, specifically Form 1040 using interactive step-by-step conversations and following the custom instructions, actions and knowledge base religiously."
SESSION_EXPIRY_MINUTES = 30
MAX_TOKENS_BEFORE_SUMMARY = 10000  # Customize as needed

# FastAPI Router
router = APIRouter()

# In-memory session store
session_store = {}

# OpenAI client with logs
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=httpx.Client(event_hooks={
        "request": [lambda req: print(f"Request: {req.method} {req.url}")],
        "response": [lambda res: print(f"Response: {res.status_code} {res.url}")]
    })
)

# Token counter
enc = tiktoken.encoding_for_model("gpt-4")

# Pydantic Models
class StartSessionRequest(BaseModel):
    session_id: str

class MessageRequest(BaseModel):
    session_id: str
    message: str

class ClearSessionRequest(BaseModel):
    session_id: str

def is_expired(last_active):
    return datetime.utcnow() - last_active > timedelta(minutes=SESSION_EXPIRY_MINUTES)

def count_tokens(messages):
    return sum(len(enc.encode(msg["content"])) for msg in messages)

def summarize_messages(messages):
    summary_prompt = "Summarize this conversation briefly:\n\n" + \
        "\n".join(f"{msg['role']}: {msg['content']}" for msg in messages)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": summary_prompt}]
    )

    summary_text = response.choices[0].message.content
    return {"role": "assistant", "content": f"Summary of earlier: {summary_text}"}

@router.post("/start-session")
def start_session(req: StartSessionRequest):
    thread = client.beta.threads.create(messages=[{
        "role": "assistant",
        "content": SYSTEM_PROMPT
    }])
    session_store[req.session_id] = {
        "thread_id": thread.id,
        "last_active": datetime.utcnow(),
        "messages": [{"role": "assistant", "content": SYSTEM_PROMPT}]
    }
    return {"session_id": req.session_id, "thread_id": thread.id}

@router.post("/send-message")
def send_message(req: MessageRequest):
    session = session_store.get(req.session_id)

    if not session or is_expired(session["last_active"]):
        # Renew session
        thread = client.beta.threads.create(messages=[{
            "role": "assistant",
            "content": SYSTEM_PROMPT
        }])
        session = {
            "thread_id": thread.id,
            "last_active": datetime.utcnow(),
            "messages": [{"role": "assistant", "content": SYSTEM_PROMPT}]
        }
        session_store[req.session_id] = session

    session["last_active"] = datetime.utcnow()
    thread_id = session["thread_id"]
    messages = session["messages"]

    # Add new user message
    messages.append({"role": "user", "content": req.message})

    # Summarize if too long
    if count_tokens(messages) > MAX_TOKENS_BEFORE_SUMMARY:
        print("🔁 Summarizing messages...")
        summary = summarize_messages(messages[:-5])  # summarize all but last 5
        session["messages"] = [summary] + messages[-5:]
        messages = session["messages"]

    # Send to OpenAI thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=req.message,
        attachments=[{
            "file_id": FILE_ID,
            "tools": [{"type": "file_search"}]
        }]
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID
    )

    response_messages = list(client.beta.threads.messages.list(
        thread_id=thread_id,
        run_id=run.id
    ))
    reply = response_messages[0].content[0].text.value

    # Store assistant reply
    messages.append({"role": "assistant", "content": reply})

    return {"response": reply, "thread_id": thread_id}

@router.post("/clear-session")
def clear_session(req: ClearSessionRequest):
    if req.session_id in session_store:
        del session_store[req.session_id]
        return {"message": f"Session '{req.session_id}' cleared."}
    return JSONResponse(status_code=404, content={"error": "Session not found."})