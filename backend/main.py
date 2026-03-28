from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from llm_service import LLMService

app = FastAPI(title="AI Accountability Coach API V2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = LLMService()

@app.on_event("startup")
async def startup_event():
    await llm.initialize_assistant()

class MessageRequest(BaseModel):
    content: str
    current_state: Optional[Dict[str, Any]] = None

@app.get("/")
def read_root():
    return {"status": "ok", "version": "v2", "mode": "Real" if llm.client else "Mock"}

import json
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
THREAD_FILE = DATA_DIR / "thread.json"

@app.get("/api/thread/active")
async def get_active_thread():
    # 1. Try to read existing thread from file
    if THREAD_FILE.exists():
        try:
            with open(THREAD_FILE, "r") as f:
                data = json.load(f)
                # Validate it looks real?
                if "id" in data:
                    return data
        except Exception as e:
            print(f"Error reading thread file: {e}")
            # Fallthrough to create new

    # 2. Create new if missing or corrupt
    new_thread = await llm.create_thread()
    
    # 3. Save to file
    try:
        with open(THREAD_FILE, "w") as f:
            json.dump(new_thread, f)
    except Exception as e:
        print(f"Error saving thread file: {e}")
        
    return new_thread

@app.post("/api/threads")
async def create_thread():
    try:
        # Force create new (e.g. for hard reset)
        data = await llm.create_thread()
        # Update the file too, so "active" becomes this new one
        with open(THREAD_FILE, "w") as f:
            json.dump(data, f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/thread/active")
async def delete_active_thread():
    try:
        if THREAD_FILE.exists():
            THREAD_FILE.unlink()
            return {"status": "deleted"}
        return {"status": "not_found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/threads/{thread_id}/messages")
async def get_messages(thread_id: str):
    try:
        msgs = await llm.get_messages(thread_id)
        return msgs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/threads/{thread_id}/messages")
async def post_message(thread_id: str, request: MessageRequest):
    try:
        # With Responses API, we pass input directly to the run
        # await llm.add_message(thread_id, request.content) # Deprecated
        
        # Run assistant with state context
        response = await llm.run_thread_with_tools(
            thread_id, 
            input_text=request.content,
            current_state=request.current_state
        )
        return response
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
