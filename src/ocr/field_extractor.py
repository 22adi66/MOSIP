"""
Smart Field Extraction Module for MOSIP OCR
Extracts specific fields from OCR text using pattern matching and AI techniques
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import difflib

@dataclass
class FieldDefinition:
    """Defines a field to extract from text"""
    name: str
    keywords: List[str]  # Keywords to look for (e.g., ["name", "naam", "नाम"])
    pattern: Optional[str] = None  # Regex pattern if specific format needed
    data_type: str = "text"  # text, number, email, phone, date
    required: bool = False

@dataclass
class ExtractedField:
    """Result of field extraction"""
    field_name: str
    value: str
    confidence: float
    source_text: str  # Original text block where this was found
    bbox: Optional[List] = None  # Bounding box coordinates

class SmartFieldExtractor:
    """Extracts specific fields from OCR text intelligently"""
    
    def __init__(self):
        self.setup_predefined_fields()
        self.setup_patterns()
    
    def setup_predefined_fields(self):
        """Setup commonly used field definitions"""
        self.predefined_fields = {
            "name": FieldDefinition(
                name="Name",
                keywords=["name", "naam", "नाम", "नम", "full name", "patient name"],
                data_type="text"
            ),
            "age": FieldDefinition(
                name="Age",
                keywords=["age", "उम्र", "आयु", "years", "yrs"],
                pattern=r'\b(\d{1,3})\s*(?:years?|yrs?|साल)?\b',
                data_type="number"
            ),
            "gender": FieldDefinition(
                name="Gender",
                keywords=["gender", "sex", "लिंग", "जेंडर"],
                pattern=r'\b(male|female|m|f|पुरुष|महिला|मर्द|औरत)\b',
                data_type="text"
            ),
            "phone": FieldDefinition(
                name="Phone",
                keywords=["phone", "mobile", "contact", "फोन", "मोबाइल"],
                pattern=r'\b(\+?91[\s-]?)?[6-9]\d{2}[\s-]?\d{3}[\s-]?\d{4}\b',
                data_type="phone"
            ),
            "email": FieldDefinition(
                name="Email",
                keywords=["email", "mail", "ईमेल"],
                pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                data_type="email"
            ),
            "address": FieldDefinition(
                name="Address",
                keywords=["address", "addr", "पता", "address:", "पता:"],
                data_type="text"
            ),
            "id_number": FieldDefinition(
                name="ID Number",
                keywords=["id", "number", "no", "आईडी", "संख्या"],
                pattern=r'\b[A-Z0-9]{4,}\b',
                data_type="text"
            ),
            "date": FieldDefinition(
                name="Date",
                keywords=["date", "dated", "तारीख", "दिनांक"],
                pattern=r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{2,4}[/-]\d{1,2}[/-]\d{1,2}\b',
                data_type="date"
            )
        }
    
    def setup_patterns(self):
        """Setup regex patterns for different data types"""
        self.patterns = {
            "phone": r'\b(\+?91[\s-]?)?[6-9]\d{2}[\s-]?\d{3}[\s-]?\d{4}\b',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "number": r'\b\d+\b',
            "date": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{2,4}[/-]\d{1,2}[/-]\d{1,2}\b',
            "alphanumeric": r'\b[A-Z0-9]{4,}\b'
        }
    
    def extract_fields(self, text_blocks: List[Dict], field_definitions: List[Dict]) -> List[ExtractedField]:
        """Extract specified fields from OCR text blocks"""
        extracted_fields = []
        
        # Convert field definitions to FieldDefinition objects
        fields_to_extract = []
        for field_def in field_definitions:
            if field_def["name"].lower() in self.predefined_fields:
                # Use predefined field with user's keywords
                predefined = self.predefined_fields[field_def["name"].lower()]
                field = FieldDefinition(
                    name=field_def["name"],
                    keywords=field_def.get("keywords", predefined.keywords),
                    pattern=predefined.pattern,
                    data_type=predefined.data_type,
                    required=field_def.get("required", False)
                )
            else:
                # Create custom field
                field = FieldDefinition(
                    name=field_def["name"],
                    keywords=field_def.get("keywords", [field_def["name"].lower()]),
                    pattern=field_def.get("pattern"),
                    data_type=field_def.get("data_type", "text"),
                    required=field_def.get("required", False)
                )
            fields_to_extract.append(field)
        
        # Extract each field
        for field in fields_to_extract:
            result = self._extract_single_field(field, text_blocks)
            if result:
                extracted_fields.append(result)
        
        return extracted_fields
    
    def _extract_single_field(self, field: FieldDefinition, text_blocks: List[Dict]) -> Optional[ExtractedField]:
        """Extract a single field from text blocks"""
        best_match = None
        best_confidence = 0.0
        
        for block in text_blocks:
            text = block["text"].lower()
            
            # Look for keyword matches
            keyword_found = False
            for keyword in field.keywords:
                if keyword.lower() in text:
                    keyword_found = True
                    break
            
            if keyword_found:
                # Try to extract value after the keyword
                value, confidence = self._extract_value_after_keyword(
                    block["text"], field.keywords, field.pattern, field.data_type
                )
                
                if value and confidence > best_confidence:
                    best_match = ExtractedField(
                        field_name=field.name,
                        value=value,
                        confidence=confidence,
                        source_text=block["text"],
                        bbox=block.get("bbox")
                    )
                    best_confidence = confidence
        
        return best_match
    
    def _extract_value_after_keyword(self, text: str, keywords: List[str], pattern: Optional[str], data_type: str) -> tuple:
        """Extract value after finding a keyword"""
        text_lower = text.lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in text_lower:
                # Find the position after the keyword
                keyword_pos = text_lower.find(keyword_lower)
                after_keyword = text[keyword_pos + len(keyword):]
                
                # Clean up the text after keyword
                after_keyword = re.sub(r'^[\s:,-]+', '', after_keyword)
                
                # Extract based on pattern or data type
                if pattern:
                    match = re.search(pattern, after_keyword, re.IGNORECASE)
                    if match:
                        return match.group(1) if match.groups() else match.group(0), 0.9
                else:
                    # Extract based on data type
                    if data_type == "phone":
                        match = re.search(self.patterns["phone"], after_keyword)
                        if match:
                            return match.group(0), 0.9
                    elif data_type == "email":
                        match = re.search(self.patterns["email"], after_keyword)
                        if match:
                            return match.group(0), 0.95
                    elif data_type == "number":
                        match = re.search(self.patterns["number"], after_keyword)
                        if match:
                            return match.group(0), 0.8
                    elif data_type == "date":
                        match = re.search(self.patterns["date"], after_keyword)
                        if match:
                            return match.group(0), 0.85
                    else:  # text
                        # Extract next word(s) for text fields
                        words = after_keyword.split()
                        if words:
                            # Take first 1-3 words depending on field
                            if any(k in keyword_lower for k in ["name", "naam", "नाम"]):
                                value = " ".join(words[:3]).strip()  # Names can be 2-3 words
                            else:
                                value = words[0].strip()  # Single word for others
                            
                            # Clean up value
                            value = re.sub(r'[^\w\s.-]', '', value).strip()
                            if value:
                                return value, 0.7
        
        return None, 0.0
    
    def get_available_fields(self) -> List[Dict]:
        """Get list of available predefined fields"""
        return [
            {
                "name": field.name,
                "keywords": field.keywords,
                "data_type": field.data_type,
                "pattern": field.pattern
            }
            for field in self.predefined_fields.values()
        ]