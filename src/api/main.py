"""
MOSIP OCR API - FastAPI Application
Main entry point for the OCR REST API service
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import tempfile
import logging
from typing import Optional, List
import time
from datetime import datetime

from .routes import router
from ..utils.config import config
from ..utils.logger import setup_logger

# Setup logger
logger = setup_logger("mosip_ocr.main")

# Create FastAPI app
app = FastAPI(
    title="MOSIP OCR API",
    description="Optical Character Recognition API for text extraction and verification",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "MOSIP OCR API",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "docs": "/api/docs",
            "health": "/health",
            "ocr_extract": "/api/v1/ocr/extract",
            "ocr_validate": "/api/v1/ocr/validate",
            "document_process": "/api/v1/document/process"
        }
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time(),
        "services": {
            "ocr_engine": "ready",
            "validator": "ready",
            "preprocessor": "ready"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.api_host,
        port=config.api_port,
        reload=True,
        log_level="info"
    )