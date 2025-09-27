#!/usr/bin/env python3
"""
Simple test server to check CORS functionality
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Add CORS
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
def read_root():
    return {"message": "Test server is working!"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/test")
def test_endpoint(request: TestRequest):
    return {"received": request.message, "response": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)