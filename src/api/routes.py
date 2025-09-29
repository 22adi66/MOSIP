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
from ..ocr.field_extractor import SmartFieldExtractor
from .models import OCRRequest, OCRResponse, ValidationRequest, ValidationResponse, DocumentProcessRequest
from ..utils.logger import setup_logger

# Setup logger
logger = setup_logger("mosip_ocr.api")

# Create router
router = APIRouter()

# Initialize OCR components (singleton pattern)
ocr_engine = None
text_validator = None
field_extractor = None
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

def get_field_extractor():
    """Get or create field extractor instance"""
    global field_extractor
    if field_extractor is None:
        field_extractor = SmartFieldExtractor()
        logger.info("Field Extractor initialized for API")
    return field_extractor

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
        # Validate file type (handle None content_type from Streamlit)
        content_type = file.content_type or ''
        filename = file.filename or ''
        
        # Check content type or file extension
        is_image = (content_type.startswith('image/') or 
                   filename.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp')))
        
        if not is_image:
            raise HTTPException(status_code=400, detail="File must be an image (JPG, PNG, TIFF, etc.)")
        
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
                    "text": str(result.text),
                    "confidence": float(result.confidence),
                    "bbox": [[int(x) for x in point] for point in result.bbox],
                    "language": str(result.language) if result.language else None
                })
            
            processing_time = time.time() - start_time
            
            response = {
                "status": "success",
                "processing_time": round(float(processing_time), 3),
                "text_blocks_found": int(len(text_blocks)),
                "text_blocks": text_blocks,
                "combined_text": str(" ".join([block["text"] for block in text_blocks])),
                "average_confidence": round(
                    float(sum(block["confidence"] for block in text_blocks) / len(text_blocks)) if text_blocks else 0.0, 3
                ),
                "parameters": {
                    "confidence_threshold": float(confidence_threshold),
                    "preprocess": bool(preprocess),
                    "languages": str(languages).split(",")
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
        # Validate file type (handle None content_type from Streamlit)
        content_type = file.content_type or ''
        filename = file.filename or ''
        
        # Check content type or file extension
        is_image = (content_type.startswith('image/') or 
                   filename.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp')))
        
        if not is_image:
            raise HTTPException(status_code=400, detail="File must be an image (JPG, PNG, TIFF, etc.)")
        
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
                    "text": str(result.text),
                    "confidence": float(result.confidence),
                    "bbox": [[int(x) for x in point] for point in result.bbox],
                    "language": str(result.language) if result.language else None
                }
                
                # Add validation if enabled
                if validator:
                    validation = validator.validate_text(result.text)
                    block_data["validation"] = {
                        "is_valid": bool(validation["valid"]),
                        "message": str(validation["message"]),
                        "rules_passed": int(validation["rules_passed"]),
                        "rules_failed": int(validation["rules_failed"])
                    }
                
                processed_blocks.append(block_data)
            
            # Generate summary
            processing_time = time.time() - start_time
            valid_blocks = [b for b in processed_blocks if not validate_fields or b.get("validation", {}).get("is_valid", True)]
            
            response = {
                "status": "success",
                "processing_time": round(float(processing_time), 3),
                "document_type": str(document_type) if document_type else None,
                "summary": {
                    "total_blocks": int(len(processed_blocks)),
                    "valid_blocks": int(len(valid_blocks)),
                    "average_confidence": round(
                        float(sum(b["confidence"] for b in processed_blocks) / len(processed_blocks)) if processed_blocks else 0.0, 3
                    ),
                    "combined_text": str(" ".join([b["text"] for b in valid_blocks]))
                },
                "text_blocks": processed_blocks,
                "parameters": {
                    "confidence_threshold": float(confidence_threshold),
                    "validate_fields": bool(validate_fields),
                    "document_type": str(document_type) if document_type else None
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

@router.get("/fields/available")
async def get_available_fields():
    """Get list of available predefined fields for extraction"""
    try:
        extractor = get_field_extractor()
        fields = extractor.get_available_fields()
        
        return {
            "status": "success",
            "available_fields": fields,
            "total_count": len(fields)
        }
        
    except Exception as e:
        logger.error(f"Failed to get available fields: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get available fields")

@router.post("/fields/extract")
async def extract_custom_fields(
    file: UploadFile = File(...),
    fields: str = Form(...),  # JSON string of field definitions
    confidence_threshold: Optional[float] = Form(0.7)
):
    """
    Extract custom fields from uploaded document
    
    **Parameters:**
    - **file**: Document image file
    - **fields**: JSON array of field definitions [{"name": "Name", "keywords": ["name", "naam"], "required": true}]
    - **confidence_threshold**: Minimum confidence score for OCR
    
    **Returns:**
    - JSON with extracted field values and their locations
    """
    start_time = time.time()
    
    try:
        # Validate file type (handle None content_type from Streamlit)
        content_type = file.content_type or ''
        filename = file.filename or ''
        
        # Check content type or file extension
        is_image = (content_type.startswith('image/') or 
                   filename.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp')))
        
        if not is_image:
            raise HTTPException(status_code=400, detail="File must be an image (JPG, PNG, TIFF, etc.)")
        
        # Parse field definitions
        try:
            import json
            field_definitions = json.loads(fields)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid field definitions JSON")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Extract text first
            loop = asyncio.get_event_loop()
            ocr_results = await loop.run_in_executor(
                executor, 
                process_image_sync, 
                temp_path, 
                confidence_threshold
            )
            
            # Convert OCR results to format expected by field extractor
            text_blocks = []
            for result in ocr_results:
                text_blocks.append({
                    "text": str(result.text),
                    "confidence": float(result.confidence),
                    "bbox": [[int(x) for x in point] for point in result.bbox],
                    "language": str(result.language) if result.language else None
                })
            
            # Extract fields
            extractor = get_field_extractor()
            extracted_fields = extractor.extract_fields(text_blocks, field_definitions)
            
            # Format response
            processing_time = time.time() - start_time
            
            fields_result = []
            for field in extracted_fields:
                fields_result.append({
                    "field_name": field.field_name,
                    "value": field.value,
                    "confidence": float(field.confidence),
                    "source_text": field.source_text,
                    "bbox": field.bbox
                })
            
            response = {
                "status": "success",
                "processing_time": round(float(processing_time), 3),
                "total_fields_requested": int(len(field_definitions)),
                "fields_extracted": int(len(fields_result)),
                "extracted_fields": fields_result,
                "original_text_blocks": text_blocks,
                "field_definitions": field_definitions
            }
            
            logger.info(f"Field extraction completed: {len(fields_result)}/{len(field_definitions)} fields extracted")
            return response
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        logger.error(f"Field extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Field extraction failed: {str(e)}")