#!/usr/bin/env python3
"""
Debug script to test the document processing endpoint locally
"""

import sys
import os
sys.path.append('.')

import asyncio
import tempfile
from src.api.routes import process_document
from fastapi import UploadFile
import io

async def test_document_processing():
    """Test the document processing function directly"""
    print("Testing document processing function directly...")
    
    try:
        # Read the test image
        with open('test_document.jpg', 'rb') as f:
            image_data = f.read()
        
        # Create a mock UploadFile object
        file_like = io.BytesIO(image_data)
        file_like.name = 'test_document.jpg'
        
        # Create UploadFile manually
        upload_file = UploadFile(
            filename='test_document.jpg',
            file=file_like,
            size=len(image_data),
            headers={'content-type': 'image/jpeg'}
        )
        
        print("Created UploadFile object")
        print(f"Content type: {upload_file.content_type}")
        print(f"Filename: {upload_file.filename}")
        print(f"Size: {upload_file.size}")
        
        # Call the function directly
        result = await process_document(
            file=upload_file,
            document_type="identity",
            confidence_threshold=0.7,
            validate_fields=True
        )
        
        print("SUCCESS!")
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_document_processing())