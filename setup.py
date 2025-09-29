"""Setup script for MOSIP OCR System"""

from setuptools import setup, find_packages
import os

# Read README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mosip-ocr",
    version="1.0.0",
    author="MOSIP OCR Team",
    author_email="ocr-team@mosip.io",
    description="OCR Text Extraction and Verification System for MOSIP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mosip/ocr-system",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Text Processing",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "gpu": ["torch>=2.0.0", "torchvision>=0.15.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-benchmark>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mosip-ocr=api.main:main",
            "mosip-ocr-test=tests.test_cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.yaml", "*.md"],
    },
    zip_safe=False,
)