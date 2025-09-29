"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class OCRRequest(BaseModel):
    """Request model for OCR text extraction"""
    confidence_threshold: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Minimum confidence score")
    preprocess: Optional[bool] = Field(True, description="Enable image preprocessing")
    languages: Optional[List[str]] = Field(["en"], description="List of language codes")

class TextBlock(BaseModel):
    """Model for extracted text block"""
    text: str = Field(..., description="Extracted text content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="OCR confidence score")
    bbox: List[List[int]] = Field(..., description="Bounding box coordinates")
    language: Optional[str] = Field(None, description="Detected language")

class ValidationResult(BaseModel):
    """Model for text validation result"""
    is_valid: bool = Field(..., description="Whether text passed validation")
    message: str = Field(..., description="Validation message")
    rules_passed: int = Field(..., description="Number of validation rules passed")
    rules_failed: int = Field(..., description="Number of validation rules failed")

class OCRResponse(BaseModel):
    """Response model for OCR text extraction"""
    status: str = Field(..., description="Response status")
    processing_time: float = Field(..., description="Processing time in seconds")
    text_blocks_found: int = Field(..., description="Number of text blocks found")
    text_blocks: List[TextBlock] = Field(..., description="Extracted text blocks")
    combined_text: str = Field(..., description="All text combined")
    average_confidence: float = Field(..., description="Average confidence score")
    parameters: Dict[str, Any] = Field(..., description="Processing parameters used")

class ValidationRequest(BaseModel):
    """Request model for text validation"""
    text: str = Field(..., min_length=1, description="Text to validate")
    document_type: Optional[str] = Field(None, description="Expected document type")
    field_type: Optional[str] = Field(None, description="Specific field type")

class ValidationResponse(BaseModel):
    """Response model for text validation"""
    status: str = Field(..., description="Response status")
    text: str = Field(..., description="Original text")
    is_valid: bool = Field(..., description="Validation result")
    validation_message: str = Field(..., description="Validation message")
    rules_passed: int = Field(..., description="Rules passed")
    rules_failed: int = Field(..., description="Rules failed")
    rule_details: List[Dict] = Field(..., description="Detailed rule results")

class DocumentProcessRequest(BaseModel):
    """Request model for complete document processing"""
    document_type: Optional[str] = Field(None, description="Expected document type")
    confidence_threshold: Optional[float] = Field(0.7, ge=0.0, le=1.0)
    validate_fields: Optional[bool] = Field(True, description="Enable field validation")

class DocumentSummary(BaseModel):
    """Summary of document processing results"""
    total_blocks: int = Field(..., description="Total text blocks found")
    valid_blocks: int = Field(..., description="Valid text blocks")
    average_confidence: float = Field(..., description="Average confidence score")
    combined_text: str = Field(..., description="Combined valid text")

class DocumentProcessResponse(BaseModel):
    """Response model for complete document processing"""
    status: str = Field(..., description="Response status")
    processing_time: float = Field(..., description="Total processing time")
    document_type: Optional[str] = Field(None, description="Document type")
    summary: DocumentSummary = Field(..., description="Processing summary")
    text_blocks: List[Dict] = Field(..., description="Detailed text blocks with validation")
    parameters: Dict[str, Any] = Field(..., description="Processing parameters")

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Response timestamp")
    services: Dict[str, Any] = Field(..., description="Service components status")

class LanguageResponse(BaseModel):
    """Language support response model"""
    status: str = Field(..., description="Response status")
    supported_languages: Dict[str, str] = Field(..., description="Language code to name mapping")
    default: str = Field(..., description="Default language")
    total_count: int = Field(..., description="Total supported languages")