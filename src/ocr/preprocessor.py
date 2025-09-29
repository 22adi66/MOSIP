"""Image Preprocessing Utilities for OCR"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from typing import Union, Tuple, Optional
import logging

logger = logging.getLogger("mosip_ocr.preprocessor")


class ImagePreprocessor:
    """Image preprocessing utilities for better OCR results"""
    
    def __init__(self, 
                 enhance_contrast: bool = True,
                 denoise: bool = True,
                 resize_factor: float = 2.0,
                 auto_rotate: bool = True):
        """Initialize preprocessor with configuration
        
        Args:
            enhance_contrast: Whether to enhance image contrast
            denoise: Whether to apply denoising
            resize_factor: Factor to resize image (>1 for upscaling)
            auto_rotate: Whether to auto-correct rotation
        """
        self.enhance_contrast = enhance_contrast
        self.denoise = denoise
        self.resize_factor = resize_factor
        self.auto_rotate = auto_rotate
        
        logger.info(f"ImagePreprocessor initialized with settings: "
                   f"contrast={enhance_contrast}, denoise={denoise}, "
                   f"resize_factor={resize_factor}, auto_rotate={auto_rotate}")
    
    def preprocess(self, image: Union[str, np.ndarray, Image.Image]) -> np.ndarray:
        """Main preprocessing pipeline
        
        Args:
            image: Input image (file path, numpy array, or PIL Image)
        
        Returns:
            Preprocessed image as numpy array
        """
        try:
            # Load and convert image
            img = self._load_image(image)
            logger.debug(f"Loaded image with shape: {img.shape}")
            
            # Apply preprocessing steps
            if self.auto_rotate:
                img = self._auto_rotate(img)
                logger.debug("Applied auto-rotation")
            
            if self.denoise:
                img = self._denoise(img)
                logger.debug("Applied denoising")
            
            if self.enhance_contrast:
                img = self._enhance_contrast(img)
                logger.debug("Applied contrast enhancement")
            
            if self.resize_factor != 1.0:
                img = self._resize(img, self.resize_factor)
                logger.debug(f"Resized image by factor {self.resize_factor}")
            
            logger.info("Image preprocessing completed successfully")
            return img
            
        except Exception as e:
            logger.error(f"Error in image preprocessing: {str(e)}")
            raise
    
    def _load_image(self, image: Union[str, np.ndarray, Image.Image]) -> np.ndarray:
        """Load image from various input types
        
        Args:
            image: Input image
        
        Returns:
            Image as numpy array in BGR format
        """
        if isinstance(image, str):
            # Load from file path
            img = cv2.imread(image)
            if img is None:
                raise ValueError(f"Could not load image from path: {image}")
        elif isinstance(image, np.ndarray):
            # Already a numpy array
            img = image.copy()
        elif isinstance(image, Image.Image):
            # Convert PIL Image to numpy array
            img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        else:
            raise TypeError(f"Unsupported image type: {type(image)}")
        
        return img
    
    def _auto_rotate(self, image: np.ndarray) -> np.ndarray:
        """Auto-correct image rotation using text line detection
        
        Args:
            image: Input image
        
        Returns:
            Rotated image
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Find lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None:
                # Calculate average angle
                angles = []
                for rho, theta in lines[:10]:  # Use first 10 lines
                    angle = theta * 180 / np.pi
                    # Convert to rotation angle
                    if angle > 90:
                        angle = angle - 180
                    angles.append(angle)
                
                if angles:
                    rotation_angle = np.median(angles)
                    
                    # Only rotate if angle is significant (>1 degree)
                    if abs(rotation_angle) > 1:
                        return self._rotate_image(image, rotation_angle)
            
            return image
            
        except Exception as e:
            logger.warning(f"Auto-rotation failed, using original image: {str(e)}")
            return image
    
    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by specified angle
        
        Args:
            image: Input image
            angle: Rotation angle in degrees
        
        Returns:
            Rotated image
        """
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        
        # Get rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Calculate new bounding dimensions
        cos_angle = abs(rotation_matrix[0, 0])
        sin_angle = abs(rotation_matrix[0, 1])
        new_width = int((height * sin_angle) + (width * cos_angle))
        new_height = int((height * cos_angle) + (width * sin_angle))
        
        # Adjust rotation matrix for new center
        rotation_matrix[0, 2] += (new_width / 2) - center[0]
        rotation_matrix[1, 2] += (new_height / 2) - center[1]
        
        # Perform rotation
        rotated = cv2.warpAffine(image, rotation_matrix, (new_width, new_height), 
                                flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        return rotated
    
    def _denoise(self, image: np.ndarray) -> np.ndarray:
        """Apply denoising to image
        
        Args:
            image: Input image
        
        Returns:
            Denoised image
        """
        # Apply Non-Local Means denoising
        if len(image.shape) == 3:
            # Color image
            denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        else:
            # Grayscale image
            denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
        
        return denoised
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance image contrast using CLAHE
        
        Args:
            image: Input image
        
        Returns:
            Contrast-enhanced image
        """
        # Convert to LAB color space for better contrast enhancement
        if len(image.shape) == 3:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_channel = clahe.apply(l_channel)
            
            # Merge channels and convert back
            enhanced = cv2.merge([l_channel, a_channel, b_channel])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        else:
            # Grayscale image
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)
        
        return enhanced
    
    def _resize(self, image: np.ndarray, factor: float) -> np.ndarray:
        """Resize image by specified factor
        
        Args:
            image: Input image
            factor: Resize factor (>1 for upscaling, <1 for downscaling)
        
        Returns:
            Resized image
        """
        height, width = image.shape[:2]
        new_width = int(width * factor)
        new_height = int(height * factor)
        
        # Use different interpolation based on scaling direction
        if factor > 1:
            # Upscaling - use cubic interpolation
            interpolation = cv2.INTER_CUBIC
        else:
            # Downscaling - use area interpolation
            interpolation = cv2.INTER_AREA
        
        resized = cv2.resize(image, (new_width, new_height), interpolation=interpolation)
        return resized
    
    def convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale
        
        Args:
            image: Input image
        
        Returns:
            Grayscale image
        """
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image
    
    def threshold_image(self, image: np.ndarray, method: str = "adaptive") -> np.ndarray:
        """Apply thresholding to create binary image
        
        Args:
            image: Input image (should be grayscale)
            method: Thresholding method ("adaptive", "otsu", "binary")
        
        Returns:
            Binary image
        """
        if len(image.shape) == 3:
            image = self.convert_to_grayscale(image)
        
        if method == "adaptive":
            return cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        elif method == "otsu":
            _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return binary
        elif method == "binary":
            _, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
            return binary
        else:
            raise ValueError(f"Unknown thresholding method: {method}")