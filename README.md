# MOSIP OCR Text Extraction and Verification System

## Overview

This project implements an Optical Character Recognition (OCR) system for text extraction and verification as part of the MOSIP (Modular Open Source Identity Platform) ecosystem. The system uses EasyOCR for efficient and accurate text extraction from identity documents.

## Features

- **Multi-language OCR** - Supports 80+ languages including English, Hindi, and regional Indian languages
- **High Accuracy** - Deep learning-based text recognition with confidence scoring
- **Document Verification** - Automated validation of extracted text fields
- **RESTful API** - Easy integration with MOSIP services
- **Real-time Processing** - Fast text extraction and verification
- **GPU Acceleration** - Optional CUDA support for enhanced performance

## Technology Stack

- **Python 3.8+**
- **EasyOCR** - Primary OCR engine
- **FastAPI** - Web framework for REST APIs
- **OpenCV** - Image preprocessing
- **Pillow** - Image handling
- **Pydantic** - Data validation
- **Docker** - Containerization

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Image Input   │───▶│  OCR Processing │───▶│  Text Output    │
│                 │    │                 │    │                 │
│ • ID Cards      │    │ • EasyOCR       │    │ • Extracted     │
│ • Passports     │    │ • Preprocessing │    │   Text          │
│ • Documents     │    │ • Enhancement   │    │ • Confidence    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Verification   │
                       │                 │
                       │ • Field Valid.  │
                       │ • Format Check  │
                       │ • Quality Score │
                       └─────────────────┘
```

## Project Structure

```
MOSIP/
├── src/
│   ├── ocr/
│   │   ├── __init__.py
│   │   ├── engine.py           # EasyOCR wrapper
│   │   ├── preprocessor.py     # Image preprocessing
│   │   └── validator.py        # Text validation
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI application
│   │   ├── routes.py          # API endpoints
│   │   └── models.py          # Pydantic models
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   └── logger.py          # Logging setup
│   └── tests/
│       ├── __init__.py
│       ├── test_ocr.py
│       └── test_api.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── config/
│   ├── config.yaml
│   └── logging.yaml
├── sample_images/
│   └── test_documents/
├── requirements.txt
├── setup.py
├── README.md
└── .env.example
```

## Implementation Plan

### Phase 1: Core OCR Engine (Week 1)
- [x] Project setup and virtual environment
- [ ] Install and configure EasyOCR
- [ ] Implement basic OCR engine wrapper
- [ ] Add image preprocessing utilities
- [ ] Create configuration management

### Phase 2: Text Processing & Validation (Week 2)
- [ ] Implement text extraction pipeline
- [ ] Add confidence scoring and filtering
- [ ] Create validation rules for common document fields
- [ ] Implement text cleaning and normalization

### Phase 3: API Development (Week 3)
- [ ] Design REST API endpoints
- [ ] Implement FastAPI application
- [ ] Add request/response models
- [ ] Create error handling and logging

### Phase 4: Integration & Testing (Week 4)
- [ ] Write comprehensive unit tests
- [ ] Performance testing and optimization
- [ ] Docker containerization
- [ ] API documentation generation

### Phase 5: MOSIP Integration (Week 5)
- [ ] MOSIP service integration
- [ ] Database connectivity
- [ ] Audit logging
- [ ] Production deployment

## Quick Start

### Prerequisites
```bash
# Python 3.8 or higher
python --version

# Virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd MOSIP

# Install dependencies
pip install -r requirements.txt

# Install EasyOCR (downloads models on first use)
python -c "import easyocr; reader = easyocr.Reader(['en'])"
```

### Basic Usage
```python
from src.ocr.engine import OCREngine

# Initialize OCR engine
ocr = OCREngine(languages=['en', 'hi'])

# Extract text from image
results = ocr.extract_text('path/to/document.jpg')

# Process results
for result in results:
    print(f"Text: {result.text}")
    print(f"Confidence: {result.confidence}")
    print(f"Coordinates: {result.bbox}")
```

### API Usage
```bash
# Start the API server
python src/api/main.py

# Test endpoint
curl -X POST "http://localhost:8000/ocr/extract" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@sample_image.jpg"
```

## Configuration

### Environment Variables
```bash
# .env file
OCR_LANGUAGES=en,hi,ta,te,kn,ml,gu,pa,bn,or,as
OCR_GPU_ENABLED=false
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### OCR Configuration
```yaml
# config/config.yaml
ocr:
  languages: ['en', 'hi']
  confidence_threshold: 0.8
  gpu_enabled: false
  
preprocessing:
  enhance_contrast: true
  denoise: true
  resize_factor: 2.0

validation:
  min_text_length: 2
  max_text_length: 1000
  allowed_chars: "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -.,/"
```

## API Endpoints

### Text Extraction
```http
POST /api/v1/ocr/extract
Content-Type: multipart/form-data

Response:
{
  "status": "success",
  "results": [
    {
      "text": "Extracted text",
      "confidence": 0.95,
      "bbox": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
      "validated": true
    }
  ],
  "processing_time": 1.23
}
```

### Document Verification
```http
POST /api/v1/verify/document
Content-Type: multipart/form-data

Response:
{
  "status": "success",
  "verification_result": {
    "document_type": "aadhaar",
    "fields_extracted": 8,
    "fields_validated": 7,
    "overall_confidence": 0.89,
    "validation_errors": []
  }
}
```

## Performance Expectations

- **Processing Speed**: ~2-5 seconds per document (CPU)
- **Processing Speed**: ~0.5-1 second per document (GPU)
- **Accuracy**: 85-95% for clear documents
- **Languages**: 80+ supported languages
- **File Formats**: JPG, PNG, TIFF, PDF (image-based)

## Supported Document Types

- **Aadhaar Cards**
- **PAN Cards**
- **Driver's License**
- **Passports**
- **Voter ID Cards**
- **Custom Document Types** (configurable)

## Testing

```bash
# Run all tests
python -m pytest src/tests/

# Run specific test categories
python -m pytest src/tests/test_ocr.py -v
python -m pytest src/tests/test_api.py -v

# Performance testing
python -m pytest src/tests/test_performance.py --benchmark
```

## Docker Deployment

```bash
# Build image
docker build -f docker/Dockerfile -t mosip-ocr:latest .

# Run container
docker run -p 8000:8000 \
  -e OCR_LANGUAGES=en,hi \
  -e OCR_GPU_ENABLED=false \
  mosip-ocr:latest

# Using docker-compose
docker-compose -f docker/docker-compose.yml up -d
```

## Monitoring & Logging

- **Structured Logging**: JSON format for easy parsing
- **Performance Metrics**: Processing time, accuracy scores
- **Error Tracking**: Detailed error logs with context
- **Health Checks**: API endpoint monitoring

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue in the repository
- Contact the MOSIP development team
- Check the documentation wiki

## Roadmap

### v1.0 (Current)
- Basic OCR with EasyOCR
- REST API
- Document validation

### v1.1 (Planned)
- Advanced preprocessing
- Custom model training
- Batch processing

### v1.2 (Future)
- ML-based validation
- Real-time streaming
- Advanced analytics

---

**Note**: This implementation prioritizes simplicity and accuracy using EasyOCR's robust deep learning models, making it suitable for production use in the MOSIP ecosystem.