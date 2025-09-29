# 🚀 MOSIP OCR - Text Extraction & Verification System

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.118.0-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.50.0-red.svg)](https://streamlit.io)
[![EasyOCR](https://img.shields.io/badge/EasyOCR-1.7.2-orange.svg)](https://github.com/JaidedAI/EasyOCR)

A comprehensive OCR system for text extraction and verification from document images with smart field extraction capabilities.

## ✨ Features

- **🔍 Multi-Language OCR**: Support for 12+ languages including Hindi, Tamil, Telugu
- **📄 Document Processing**: Complete document analysis with validation
- **🎯 Smart Field Extraction**: Custom field definition and auto-extraction
- **✅ Text Validation**: Custom validation rules and confidence scoring
- **🌐 REST API**: FastAPI-based API with automatic documentation
- **💻 Web Interface**: Beautiful Streamlit frontend
- **🚀 Public Access**: Ngrok integration for worldwide accessibility

## 🏗️ Project Structure

```
MOSIP/
├── src/                    # Source code
│   ├── api/               # FastAPI application
│   │   ├── main.py        # API entry point
│   │   ├── routes.py      # API endpoints
│   │   └── models.py      # Pydantic models
│   ├── ocr/               # OCR processing modules
│   │   ├── engine.py      # Main OCR engine
│   │   ├── preprocessor.py # Image preprocessing
│   │   ├── validator.py   # Text validation
│   │   └── field_extractor.py # Smart field extraction
│   └── utils/             # Utility modules
│       └── logger.py      # Logging configuration
├── config/                # Configuration files
├── docs/                  # Documentation
├── sample_images/         # Test images
├── streamlit_app.py       # Frontend application
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd MOSIP

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### 3. Start the Web Interface

```bash
streamlit run streamlit_app.py
```

### 4. Access the Applications

- **API Documentation**: http://localhost:8000/docs
- **Web Interface**: http://localhost:8501
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### Core OCR Operations
- `POST /api/v1/ocr/extract` - Extract text from images
- `POST /api/v1/ocr/validate` - Validate extracted text
- `POST /api/v1/document/process` - Complete document processing

### Smart Field Extraction
- `GET /api/v1/fields/available` - Get predefined fields
- `POST /api/v1/fields/extract` - Extract custom fields

### System Information
- `GET /health` - API health check
- `GET /api/v1/languages` - Supported languages

## 🎯 Smart Field Extraction

Define custom fields to extract specific information:

```json
[
  {
    "name": "Name",
    "keywords": ["name", "naam", "नाम"],
    "data_type": "text",
    "required": true
  },
  {
    "name": "Phone",
    "keywords": ["phone", "mobile"],
    "data_type": "phone",
    "required": false
  }
]
```

## 🔧 Configuration

### Environment Variables
- `LOG_LEVEL`: Logging level (default: INFO)
- `OCR_LANGUAGES`: Default OCR languages (default: en)
- `CONFIDENCE_THRESHOLD`: Default confidence threshold (default: 0.7)

### Supported Image Formats
- JPG/JPEG
- PNG
- TIFF/TIF
- BMP

### Supported Languages
English, Hindi, Tamil, Telugu, Kannada, Malayalam, Gujarati, Punjabi, Bengali, Odia, Assamese, Urdu

## 📖 Documentation

- **[Quick Start Guide](docs/QUICK_START_FOR_FRIEND.md)** - Get started quickly
- **[API Guide](docs/STREAMLIT_API_GUIDE.md)** - Complete API documentation
- **[Problem Resolution](docs/PROBLEM_RESOLUTION_SUMMARY.md)** - Troubleshooting guide

## 🧪 Testing

Test with sample images:

```bash
# Test basic OCR
curl -X POST "http://localhost:8000/api/v1/ocr/extract" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_images/document.jpg" \
  -F "confidence_threshold=0.7"
```

## 🌟 Performance

- **Processing Speed**: ~0.3-1.0 seconds per document
- **Accuracy**: 90%+ confidence on clear documents
- **Concurrent Users**: Supports multiple simultaneous requests
- **Memory Usage**: ~500MB baseline + 200MB per active request

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the [troubleshooting guide](docs/PROBLEM_RESOLUTION_SUMMARY.md)
- Open an issue on GitHub
- Review the API documentation at `/docs`

## 🎉 Acknowledgments

- **EasyOCR** - OCR engine
- **FastAPI** - Web framework
- **Streamlit** - Frontend framework
- **OpenCV** - Image processing