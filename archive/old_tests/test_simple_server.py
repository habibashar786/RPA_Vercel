"""Simple test server to verify Uvicorn works."""
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.on_event("startup")
async def startup():
    print("✅ STARTUP EVENT CALLED")
    await asyncio.sleep(0.1)  # Simulate work
    print("✅ STARTUP EVENT COMPLETE")

if __name__ == "__main__":
    import uvicorn
    print("Starting test server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
