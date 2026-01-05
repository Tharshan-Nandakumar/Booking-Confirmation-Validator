from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import stream

import os

app = FastAPI(
    title="Booking Confirmation Validator",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream.router, tags=["Stream"])
@app.get("/utils/health-check")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    