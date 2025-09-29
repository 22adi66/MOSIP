"""
API Routes for MOSIP OCR Service
Contains all the API endpoints for text extraction and validation
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import tempfile
import os
import time
from datetime import datetime
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..ocr.engine import OCREngine
from ..ocr.validator import TextValidator
from .models import OCRRequest, OCRResponse, ValidationRequest, ValidationResponse, DocumentProcessRequest
from ..utils.logger import setup_logger

# Setup logger
logger = setup_logger("mosip_ocr.api")

# Create router
router = APIRouter()

# Initialize OCR components (singleton pattern)
ocr_engine = None
text_validator = None
executor = ThreadPoolExecutor(max_workers=4)

def get_ocr_engine():
    """Get or create OCR engine instance"""
    global ocr_engine
    if ocr_engine is None:
        ocr_engine = OCREngine(languages=['en'], gpu_enabled=False)
        logger.info("OCR Engine initialized for API")
    return ocr_engine

def get_text_validator():
    """Get or create text validator instance"""
    global text_validator
    if text_validator is None:
        text_validator = TextValidator()
        logger.info("Text Validator initialized for API")
    return text_validator

def process_image_sync(image_path: str, confidence_threshold: float = 0.7):
    """Synchronous image processing for async wrapper"""
    engine = get_ocr_engine()
    engine.confidence_threshold = confidence_threshold
    return engine.extract_text(image_path)

@router.post("/ocr/extract", response_model=OCRResponse)
async def extract_text(
    file: UploadFile = File(...),
    confidence_threshold: Optional[float] = Form(0.7),
    preprocess: Optional[bool] = Form(True),
    languages: Optional[str] = Form("en")
):
    """
    Extract text from uploaded image
    
    **Parameters:**
    - **file**: Image file (JPG, PNG, TIFF)
    - **confidence_threshold**: Minimum confidence score (0.0-1.0), default 0.7
    - **preprocess**: Enable image preprocessing, default True
    - **languages**: Comma-separated language codes, default "en"
    
    **Returns:**
    - JSON with extracted text blocks, confidence scores, and bounding boxes
    """
    start_time = time.time()
    
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Process image asynchronously
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                executor, 
                process_image_sync, 
                temp_path, 
                confidence_threshold
            )
            
            # Format response
            text_blocks = []
            for result in results:
                text_blocks.append({
                    "text": result.text,
                    "confidence": result.confidence,
                    "bbox": result.bbox,
                    "language": result.language
                })
            
            processing_time = time.time() - start_time
            
            response = {
                "status": "success",
                "processing_time": round(processing_time, 3),
                "text_blocks_found": len(text_blocks),
                "text_blocks": text_blocks,
                "combined_text": " ".join([block["text"] for block in text_blocks]),
                "average_confidence": round(
                    sum(block["confidence"] for block in text_blocks) / len(text_blocks) if text_blocks else 0, 3
                ),
                "parameters": {
                    "confidence_threshold": confidence_threshold,
                    "preprocess": preprocess,
                    "languages": languages.split(",")
                }
            }
            
            logger.info(f"OCR extraction completed: {len(text_blocks)} blocks in {processing_time:.2f}s")
            return response
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        logger.error(f"OCR extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@router.post("/ocr/validate")
async def validate_text(request: ValidationRequest):
    """
    Validate extracted text
    
    **Parameters:**
    - **text**: Text to validate
    - **document_type**: Expected document type (optional)
    - **field_type**: Specific field type to validate (optional)
    
    **Returns:**
    - Validation results with errors and warnings
    """
    try:
        validator = get_text_validator()
        
        # Validate the text
        result = validator.validate_text(request.text)
        
        response = {
            "status": "success",
            "text": request.text,
            "is_valid": result["valid"],
            "validation_message": result["message"],
            "rules_passed": result["rules_passed"],
            "rules_failed": result["rules_failed"],
            "rule_details": result["rule_results"],
            "document_type": request.document_type,
            "field_type": request.field_type
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Text validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.post("/document/process")
async def process_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    confidence_threshold: Optional[float] = Form(0.7),
    validate_fields: Optional[bool] = Form(True)
):
    """
    Complete document processing: Extract + Validate
    
    **Parameters:**
    - **file**: Document image file
    - **document_type**: Expected document type (aadhaar, pan, passport, etc.)
    - **confidence_threshold**: Minimum confidence score
    - **validate_fields**: Enable field validation
    
    **Returns:**
    - Complete processing results with extraction and validation
    """
    start_time = time.time()
    
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Extract text
            loop = asyncio.get_event_loop()
            ocr_results = await loop.run_in_executor(
                executor, 
                process_image_sync, 
                temp_path, 
                confidence_threshold
            )
            
            # Process and validate results
            processed_blocks = []
            validator = get_text_validator() if validate_fields else None
            
            for result in ocr_results:
                block_data = {
                    "text": result.text,
                    "confidence": result.confidence,
                    "bbox": result.bbox,
                    "language": result.language
                }
                
                # Add validation if enabled
                if validator:
                    validation = validator.validate_text(result.text)
                    block_data["validation"] = {
                        "is_valid": validation["valid"],
                        "message": validation["message"],
                        "rules_passed": validation["rules_passed"],
                        "rules_failed": validation["rules_failed"]
                    }
                
                processed_blocks.append(block_data)
            
            # Generate summary
            processing_time = time.time() - start_time
            valid_blocks = [b for b in processed_blocks if not validate_fields or b.get("validation", {}).get("is_valid", True)]
            
            response = {
                "status": "success",
                "processing_time": round(processing_time, 3),
                "document_type": document_type,
                "summary": {
                    "total_blocks": len(processed_blocks),
                    "valid_blocks": len(valid_blocks),
                    "average_confidence": round(
                        sum(b["confidence"] for b in processed_blocks) / len(processed_blocks) if processed_blocks else 0, 3
                    ),
                    "combined_text": " ".join([b["text"] for b in valid_blocks])
                },
                "text_blocks": processed_blocks,
                "parameters": {
                    "confidence_threshold": confidence_threshold,
                    "validate_fields": validate_fields,
                    "document_type": document_type
                }
            }
            
            logger.info(f"Document processing completed: {len(valid_blocks)}/{len(processed_blocks)} valid blocks")
            return response
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        logger.error(f"Document processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@router.get("/languages")
async def get_supported_languages():
    """Get list of supported OCR languages"""
    try:
        # Common language codes supported by EasyOCR
        languages = {
            "en": "English",
            "hi": "Hindi", 
            "ta": "Tamil",
            "te": "Telugu",
            "kn": "Kannada",
            "ml": "Malayalam",
            "gu": "Gujarati",
            "pa": "Punjabi",
            "bn": "Bengali",
            "or": "Odia",
            "as": "Assamese",
            "ur": "Urdu"
        }
        
        return {
            "status": "success",
            "supported_languages": languages,
            "default": "en",
            "total_count": len(languages)
        }
        
    except Exception as e:
        logger.error(f"Language list error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get language list")

@router.get("/health")
async def api_health_check():
    """API-specific health check"""
    try:
        # Test OCR engine
        engine = get_ocr_engine()
        validator = get_text_validator()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "ocr_engine": "ready",
                "text_validator": "ready",
                "languages": engine.get_supported_languages(),
                "confidence_threshold": engine.confidence_threshold
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }