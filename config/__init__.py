"""Configuration files for MOSIP OCR System"""

# Create config directory
import os
from pathlib import Path

config_dir = Path(__file__).parent.parent.parent / "config"
config_dir.mkdir(exist_ok=True)