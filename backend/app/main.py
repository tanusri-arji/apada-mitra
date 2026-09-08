"""
Main entry point for APADA MITRA FastAPI Backend Server.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.api.ml_routes import router as ml_router

app = FastAPI(
    title="APADA MITRA - Disaster Intelligence Backend API",
    description="Terrain-Aware Multi-Hazard Flash Flood Risk Engine (SIH Problem SIH26192)",
    version="1.0.0",
)

# Enable CORS for local React/Vite development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers under /api
app.include_router(api_router, prefix="/api")
app.include_router(ml_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "APADA MITRA API Server active.",
        "documentation": "/docs",
        "health": "/api/health",
        "data_mode": "See /api/health and /api/data-quality for live/cached/demo source state"
    }
