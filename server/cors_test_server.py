#!/usr/bin/env python3
"""
Minimal server just to test CORS issue
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="CORS Test Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TestRequest(BaseModel):
    message: str

@app.get("/")
def root():
    return {"message": "CORS test server is running"}

@app.get("/health") 
def health():
    return {"status": "ok", "cors": "enabled"}

@app.options("/langchain/process-video")
def process_video_options():
    return {"message": "OPTIONS request successful"}

@app.post("/langchain/process-video")
def process_video(request: TestRequest):
    return {"received": request.message, "status": "success", "cors": "working"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8003)