"""Configuration Management for MOSIP OCR System"""

import os
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for OCR system settings"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration
        
        Args:
            config_path: Optional path to config file. If None, uses default.
        """
        self.config_path = config_path or self._get_default_config_path()
        self._config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        current_dir = Path(__file__).parent.parent.parent
        return str(current_dir / "config" / "config.yaml")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    return yaml.safe_load(file) or {}
        except Exception as e:
            print(f"Warning: Could not load config file {self.config_path}: {e}")
        
        # Return default configuration if file loading fails
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            'ocr': {
                'languages': ['en', 'hi'],
                'confidence_threshold': 0.8,
                'gpu_enabled': False,
                'model_storage_directory': None
            },
            'preprocessing': {
                'enhance_contrast': True,
                'denoise': True,
                'resize_factor': 2.0,
                'auto_rotate': True
            },
            'validation': {
                'min_text_length': 2,
                'max_text_length': 1000,
                'allowed_chars': "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -.,/()[]"
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8000,
                'max_file_size': 10 * 1024 * 1024,  # 10MB
                'allowed_extensions': ['.jpg', '.jpeg', '.png', '.tiff', '.pdf']
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file_path': 'logs/ocr.log'
            }
        }
    
    # OCR Configuration Properties
    @property
    def ocr_languages(self) -> List[str]:
        """Get OCR languages from config or environment"""
        env_languages = os.getenv('OCR_LANGUAGES')
        if env_languages:
            return [lang.strip() for lang in env_languages.split(',')]
        return self._config.get('ocr', {}).get('languages', ['en', 'hi'])
    
    @property
    def ocr_confidence_threshold(self) -> float:
        """Get OCR confidence threshold"""
        return float(os.getenv('OCR_CONFIDENCE_THRESHOLD', 
                              self._config.get('ocr', {}).get('confidence_threshold', 0.8)))
    
    @property
    def ocr_gpu_enabled(self) -> bool:
        """Get OCR GPU enabled flag"""
        env_gpu = os.getenv('OCR_GPU_ENABLED', '').lower()
        if env_gpu in ('true', '1', 'yes'):
            return True
        elif env_gpu in ('false', '0', 'no'):
            return False
        return self._config.get('ocr', {}).get('gpu_enabled', False)
    
    @property
    def ocr_model_storage_directory(self) -> Optional[str]:
        """Get OCR model storage directory"""
        return os.getenv('OCR_MODEL_STORAGE_DIRECTORY', 
                        self._config.get('ocr', {}).get('model_storage_directory'))
    
    # Preprocessing Configuration Properties
    @property
    def preprocessing_enhance_contrast(self) -> bool:
        """Get preprocessing enhance contrast flag"""
        return self._config.get('preprocessing', {}).get('enhance_contrast', True)
    
    @property
    def preprocessing_denoise(self) -> bool:
        """Get preprocessing denoise flag"""
        return self._config.get('preprocessing', {}).get('denoise', True)
    
    @property
    def preprocessing_resize_factor(self) -> float:
        """Get preprocessing resize factor"""
        return self._config.get('preprocessing', {}).get('resize_factor', 2.0)
    
    @property
    def preprocessing_auto_rotate(self) -> bool:
        """Get preprocessing auto rotate flag"""
        return self._config.get('preprocessing', {}).get('auto_rotate', True)
    
    # Validation Configuration Properties
    @property
    def validation_min_text_length(self) -> int:
        """Get validation minimum text length"""
        return self._config.get('validation', {}).get('min_text_length', 2)
    
    @property
    def validation_max_text_length(self) -> int:
        """Get validation maximum text length"""
        return self._config.get('validation', {}).get('max_text_length', 1000)
    
    @property
    def validation_allowed_chars(self) -> str:
        """Get validation allowed characters"""
        return self._config.get('validation', {}).get('allowed_chars', 
                               "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -.,/()[]{}")
    
    # API Configuration Properties
    @property
    def api_host(self) -> str:
        """Get API host"""
        return os.getenv('API_HOST', self._config.get('api', {}).get('host', '0.0.0.0'))
    
    @property
    def api_port(self) -> int:
        """Get API port"""
        return int(os.getenv('API_PORT', self._config.get('api', {}).get('port', 8000)))
    
    @property
    def api_max_file_size(self) -> int:
        """Get API maximum file size in bytes"""
        return self._config.get('api', {}).get('max_file_size', 10 * 1024 * 1024)
    
    @property
    def api_allowed_extensions(self) -> List[str]:
        """Get API allowed file extensions"""
        return self._config.get('api', {}).get('allowed_extensions', 
                               ['.jpg', '.jpeg', '.png', '.tiff', '.pdf'])
    
    # Logging Configuration Properties
    @property
    def log_level(self) -> str:
        """Get logging level"""
        return os.getenv('LOG_LEVEL', self._config.get('logging', {}).get('level', 'INFO'))
    
    @property
    def log_format(self) -> str:
        """Get logging format"""
        return self._config.get('logging', {}).get('format', 
                               '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    @property
    def log_file_path(self) -> str:
        """Get logging file path"""
        return self._config.get('logging', {}).get('file_path', 'logs/ocr.log')
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get the complete configuration dictionary"""
        return self._config.copy()
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values
        
        Args:
            updates: Dictionary of configuration updates
        """
        def deep_update(base_dict: dict, update_dict: dict) -> dict:
            """Recursively update nested dictionaries"""
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
            return base_dict
        
        deep_update(self._config, updates)


# Global configuration instance
config = Config()