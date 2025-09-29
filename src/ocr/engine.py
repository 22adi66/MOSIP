"""EasyOCR Engine Wrapper for MOSIP OCR System"""

import easyocr
import numpy as np
from PIL import Image
from typing import List, Union, Optional, Dict, Any, Tuple
import logging
import time
from pathlib import Path

from ..utils.config import config
from .preprocessor import ImagePreprocessor

logger = logging.getLogger("mosip_ocr.engine")


class OCRResult:
    """OCR result data structure"""
    
    def __init__(self, text: str, confidence: float, bbox: List[List[int]], 
                 language: Optional[str] = None):
        """Initialize OCR result
        
        Args:
            text: Extracted text
            confidence: Confidence score (0.0 to 1.0)
            bbox: Bounding box coordinates [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            language: Detected language (if available)
        """
        self.text = text.strip()
        self.confidence = confidence
        self.bbox = bbox
        self.language = language
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bbox": self.bbox,
            "language": self.language,
            "timestamp": self.timestamp
        }
    
    def __repr__(self):
        return f"OCRResult(text='{self.text[:50]}...', confidence={self.confidence:.3f})"


class OCREngine:
    """EasyOCR engine wrapper for text extraction"""
    
    def __init__(self, 
                 languages: Optional[List[str]] = None,
                 gpu_enabled: Optional[bool] = None,
                 confidence_threshold: Optional[float] = None,
                 model_storage_directory: Optional[str] = None,
                 use_preprocessing: bool = True):
        """Initialize OCR engine
        
        Args:
            languages: List of language codes (e.g., ['en', 'hi'])
            gpu_enabled: Whether to use GPU acceleration
            confidence_threshold: Minimum confidence threshold for results
            model_storage_directory: Directory to store EasyOCR models
            use_preprocessing: Whether to use image preprocessing
        """
        # Use config values if not provided
        self.languages = languages or config.ocr_languages
        self.gpu_enabled = gpu_enabled if gpu_enabled is not None else config.ocr_gpu_enabled
        self.confidence_threshold = confidence_threshold or config.ocr_confidence_threshold
        self.model_storage_directory = model_storage_directory or config.ocr_model_storage_directory
        self.use_preprocessing = use_preprocessing
        
        # Initialize preprocessor if enabled
        self.preprocessor = None
        if self.use_preprocessing:
            self.preprocessor = ImagePreprocessor(
                enhance_contrast=config.preprocessing_enhance_contrast,
                denoise=config.preprocessing_denoise,
                resize_factor=config.preprocessing_resize_factor,
                auto_rotate=config.preprocessing_auto_rotate
            )
        
        # Initialize EasyOCR reader
        self.reader = None
        self._initialize_reader()
        
        logger.info(f"OCR Engine initialized with languages: {self.languages}, "
                   f"GPU: {self.gpu_enabled}, threshold: {self.confidence_threshold}")
    
    def _initialize_reader(self):
        """Initialize EasyOCR reader with error handling"""
        try:
            logger.info("Initializing EasyOCR reader...")
            start_time = time.time()
            
            reader_kwargs = {
                'lang_list': self.languages,
                'gpu': self.gpu_enabled
            }
            
            # Add model storage directory if specified
            if self.model_storage_directory:
                Path(self.model_storage_directory).mkdir(parents=True, exist_ok=True)
                reader_kwargs['model_storage_directory'] = self.model_storage_directory
            
            self.reader = easyocr.Reader(**reader_kwargs)
            
            init_time = time.time() - start_time
            logger.info(f"EasyOCR reader initialized successfully in {init_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR reader: {str(e)}")
            # Fallback: try without GPU
            if self.gpu_enabled:
                logger.warning("Retrying without GPU acceleration...")
                try:
                    self.reader = easyocr.Reader(lang_list=self.languages, gpu=False)
                    self.gpu_enabled = False
                    logger.info("EasyOCR reader initialized successfully without GPU")
                except Exception as fallback_error:
                    logger.error(f"Failed to initialize EasyOCR reader even without GPU: {str(fallback_error)}")
                    raise
            else:
                raise
    
    def extract_text(self, 
                    image: Union[str, np.ndarray, Image.Image],
                    confidence_threshold: Optional[float] = None,
                    detail: int = 1) -> List[OCRResult]:
        """Extract text from image
        
        Args:
            image: Input image (file path, numpy array, or PIL Image)
            confidence_threshold: Override confidence threshold for this extraction
            detail: Level of detail (0=simple text, 1=text+confidence+bbox)
        
        Returns:
            List of OCR results
        """
        if self.reader is None:
            raise RuntimeError("OCR reader not initialized")
        
        threshold = confidence_threshold or self.confidence_threshold
        
        try:
            start_time = time.time()
            
            # Preprocess image if enabled
            processed_image = image
            if self.preprocessor and not isinstance(image, str):
                processed_image = self.preprocessor.preprocess(image)
                logger.debug("Image preprocessing completed")
            
            # Extract text using EasyOCR
            logger.debug("Starting text extraction...")
            results = self.reader.readtext(processed_image, detail=detail)
            
            processing_time = time.time() - start_time
            logger.info(f"Text extraction completed in {processing_time:.2f} seconds, "
                       f"found {len(results)} text regions")
            
            # Process results
            ocr_results = []
            for result in results:
                if detail == 1:
                    bbox, text, confidence = result
                    
                    # Filter by confidence threshold
                    if confidence >= threshold:
                        ocr_result = OCRResult(
                            text=text,
                            confidence=confidence,
                            bbox=bbox,
                            language=self._detect_language(text)
                        )
                        ocr_results.append(ocr_result)
                        logger.debug(f"Accepted text: '{text}' (confidence: {confidence:.3f})")
                    else:
                        logger.debug(f"Rejected text: '{text}' (confidence: {confidence:.3f} < {threshold})")
                else:
                    # Simple text extraction (detail=0)
                    text = result
                    ocr_result = OCRResult(
                        text=text,
                        confidence=1.0,  # No confidence available in simple mode
                        bbox=[],
                        language=self._detect_language(text)
                    )
                    ocr_results.append(ocr_result)
            
            logger.info(f"Extracted {len(ocr_results)} valid text regions above threshold {threshold}")
            return ocr_results
            
        except Exception as e:
            logger.error(f"Error during text extraction: {str(e)}")
            raise
    
    def extract_text_simple(self, image: Union[str, np.ndarray, Image.Image]) -> str:
        """Extract text as a single string
        
        Args:
            image: Input image
        
        Returns:
            Concatenated extracted text
        """
        results = self.extract_text(image)
        return " ".join([result.text for result in results])
    
    def extract_text_with_structure(self, 
                                  image: Union[str, np.ndarray, Image.Image],
                                  sort_by: str = "top_to_bottom") -> List[OCRResult]:
        """Extract text with structural ordering
        
        Args:
            image: Input image
            sort_by: Sorting method ("top_to_bottom", "left_to_right", "confidence")
        
        Returns:
            Sorted list of OCR results
        """
        results = self.extract_text(image)
        
        if sort_by == "top_to_bottom":
            # Sort by top coordinate (y-axis)
            results.sort(key=lambda x: min([point[1] for point in x.bbox]) if x.bbox else 0)
        elif sort_by == "left_to_right":
            # Sort by left coordinate (x-axis)
            results.sort(key=lambda x: min([point[0] for point in x.bbox]) if x.bbox else 0)
        elif sort_by == "confidence":
            # Sort by confidence (descending)
            results.sort(key=lambda x: x.confidence, reverse=True)
        
        return results
    
    def _detect_language(self, text: str) -> Optional[str]:
        """Simple language detection based on character patterns
        
        Args:
            text: Input text
        
        Returns:
            Detected language code or None
        """
        # Simple heuristics for common languages
        if not text:
            return None
        
        # Check for Devanagari script (Hindi and other Indian languages)
        devanagari_range = range(0x0900, 0x097F)
        if any(ord(char) in devanagari_range for char in text):
            return "hi"  # Hindi
        
        # Check for Tamil script
        tamil_range = range(0x0B80, 0x0BFF)
        if any(ord(char) in tamil_range for char in text):
            return "ta"  # Tamil
        
        # Check for Telugu script
        telugu_range = range(0x0C00, 0x0C7F)
        if any(ord(char) in telugu_range for char in text):
            return "te"  # Telugu
        
        # Default to English if mostly ASCII
        if all(ord(char) < 128 for char in text):
            return "en"
        
        return None
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return self.languages.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics and configuration"""
        return {
            "languages": self.languages,
            "gpu_enabled": self.gpu_enabled,
            "confidence_threshold": self.confidence_threshold,
            "preprocessing_enabled": self.use_preprocessing,
            "model_storage_directory": self.model_storage_directory,
            "reader_initialized": self.reader is not None
        }
    
    def validate_image(self, image: Union[str, np.ndarray, Image.Image]) -> bool:
        """Validate if image can be processed
        
        Args:
            image: Input image
        
        Returns:
            True if image is valid, False otherwise
        """
        try:
            if isinstance(image, str):
                # Check if file exists and is readable
                path = Path(image)
                if not path.exists() or not path.is_file():
                    return False
                
                # Try to read the image
                test_img = Image.open(image)
                test_img.close()
                
            elif isinstance(image, np.ndarray):
                # Check if array has valid shape
                if len(image.shape) < 2 or len(image.shape) > 3:
                    return False
                if image.size == 0:
                    return False
                    
            elif isinstance(image, Image.Image):
                # Check if PIL image is valid
                if image.size[0] == 0 or image.size[1] == 0:
                    return False
            else:
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Image validation failed: {str(e)}")
            return False