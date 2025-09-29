"""Text Validation Module for OCR Results"""

import re
from typing import List, Dict, Any, Optional, Union
import logging
from datetime import datetime

from ..utils.config import config

logger = logging.getLogger("mosip_ocr.validator")


class ValidationRule:
    """Base class for validation rules"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def validate(self, text: str) -> Dict[str, Any]:
        """Validate text against this rule
        
        Args:
            text: Text to validate
        
        Returns:
            Validation result dictionary
        """
        raise NotImplementedError("Subclasses must implement validate method")


class LengthValidationRule(ValidationRule):
    """Validate text length"""
    
    def __init__(self, min_length: int = 2, max_length: int = 1000):
        super().__init__("length", f"Text length between {min_length} and {max_length}")
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, text: str) -> Dict[str, Any]:
        text_length = len(text.strip())
        is_valid = self.min_length <= text_length <= self.max_length
        
        return {
            "rule": self.name,
            "valid": is_valid,
            "message": f"Text length: {text_length}" if is_valid else 
                      f"Text length {text_length} not in range [{self.min_length}, {self.max_length}]",
            "details": {"length": text_length, "min": self.min_length, "max": self.max_length}
        }


class CharacterValidationRule(ValidationRule):
    """Validate allowed characters"""
    
    def __init__(self, allowed_chars: Optional[str] = None):
        allowed_chars = allowed_chars or config.validation_allowed_chars
        super().__init__("characters", f"Only allowed characters: {allowed_chars[:50]}...")
        self.allowed_chars = set(allowed_chars)
    
    def validate(self, text: str) -> Dict[str, Any]:
        invalid_chars = set(text) - self.allowed_chars
        is_valid = len(invalid_chars) == 0
        
        return {
            "rule": self.name,
            "valid": is_valid,
            "message": "All characters are valid" if is_valid else 
                      f"Invalid characters found: {', '.join(sorted(invalid_chars))}",
            "details": {"invalid_chars": list(invalid_chars)}
        }


class PatternValidationRule(ValidationRule):
    """Validate text against regex patterns"""
    
    def __init__(self, pattern: str, name: str, description: str, must_match: bool = True):
        super().__init__(name, description)
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.must_match = must_match
    
    def validate(self, text: str) -> Dict[str, Any]:
        match = self.pattern.search(text)
        is_valid = bool(match) if self.must_match else not bool(match)
        
        return {
            "rule": self.name,
            "valid": is_valid,
            "message": f"Pattern {'matched' if match else 'not matched'}: {self.description}",
            "details": {"pattern_matched": bool(match), "must_match": self.must_match}
        }


class AadhaarValidationRule(ValidationRule):
    """Validate Aadhaar number format"""
    
    def __init__(self):
        super().__init__("aadhaar", "Aadhaar number format validation")
        self.pattern = re.compile(r'\b\d{4}\s*\d{4}\s*\d{4}\b')
    
    def validate(self, text: str) -> Dict[str, Any]:
        # Remove spaces and check if it's 12 digits
        cleaned_text = re.sub(r'\s+', '', text)
        
        # Check if it matches Aadhaar pattern
        matches = self.pattern.findall(text)
        
        is_valid = False
        details = {"matches": matches}
        
        if matches:
            # Additional validation: check if it's exactly 12 digits
            for match in matches:
                cleaned_match = re.sub(r'\s+', '', match)
                if len(cleaned_match) == 12 and cleaned_match.isdigit():
                    # Basic checksum validation could be added here
                    is_valid = True
                    break
        
        return {
            "rule": self.name,
            "valid": is_valid,
            "message": "Valid Aadhaar format found" if is_valid else "No valid Aadhaar format found",
            "details": details
        }


class PANValidationRule(ValidationRule):
    """Validate PAN number format"""
    
    def __init__(self):
        super().__init__("pan", "PAN number format validation")
        self.pattern = re.compile(r'\b[A-Z]{5}\d{4}[A-Z]{1}\b')
    
    def validate(self, text: str) -> Dict[str, Any]:
        matches = self.pattern.findall(text.upper())
        is_valid = len(matches) > 0
        
        return {
            "rule": self.name,
            "valid": is_valid,
            "message": f"Valid PAN format found: {matches[0]}" if is_valid else "No valid PAN format found",
            "details": {"matches": matches}
        }


class DateValidationRule(ValidationRule):
    """Validate date formats"""
    
    def __init__(self):
        super().__init__("date", "Date format validation")
        self.patterns = [
            (r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b', '%d/%m/%Y'),
            (r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2}\b', '%d/%m/%y'),
            (r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b', '%Y/%m/%d'),
        ]
    
    def validate(self, text: str) -> Dict[str, Any]:
        found_dates = []
        
        for pattern, date_format in self.patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    # Try to parse the date
                    parsed_date = datetime.strptime(match.replace('-', '/'), date_format)
                    found_dates.append({
                        "original": match,
                        "parsed": parsed_date.strftime('%Y-%m-%d'),
                        "format": date_format
                    })
                except ValueError:
                    continue
        
        is_valid = len(found_dates) > 0
        
        return {
            "rule": self.name,
            "valid": is_valid,
            "message": f"Found {len(found_dates)} valid dates" if is_valid else "No valid dates found",
            "details": {"dates": found_dates}
        }


class TextValidator:
    """Main text validation class"""
    
    def __init__(self, custom_rules: Optional[List[ValidationRule]] = None):
        """Initialize validator with rules
        
        Args:
            custom_rules: Optional list of custom validation rules
        """
        self.rules = self._initialize_default_rules()
        
        if custom_rules:
            self.rules.extend(custom_rules)
        
        logger.info(f"TextValidator initialized with {len(self.rules)} rules")
    
    def _initialize_default_rules(self) -> List[ValidationRule]:
        """Initialize default validation rules"""
        return [
            LengthValidationRule(
                min_length=config.validation_min_text_length,
                max_length=config.validation_max_text_length
            ),
            CharacterValidationRule(config.validation_allowed_chars)
        ]
    
    def add_rule(self, rule: ValidationRule) -> None:
        """Add a custom validation rule
        
        Args:
            rule: Validation rule to add
        """
        self.rules.append(rule)
        logger.info(f"Added validation rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a validation rule by name
        
        Args:
            rule_name: Name of the rule to remove
        
        Returns:
            True if rule was found and removed, False otherwise
        """
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                removed_rule = self.rules.pop(i)
                logger.info(f"Removed validation rule: {removed_rule.name}")
                return True
        return False
    
    def validate_text(self, text: str, rule_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Validate text against all or specified rules
        
        Args:
            text: Text to validate
            rule_names: Optional list of rule names to apply (if None, apply all)
        
        Returns:
            Validation results dictionary
        """
        if not text or not text.strip():
            return {
                "valid": False,
                "message": "Empty or whitespace-only text",
                "rules_passed": 0,
                "rules_failed": 0,
                "rule_results": []
            }
        
        # Filter rules if rule_names is specified
        rules_to_apply = self.rules
        if rule_names:
            rules_to_apply = [rule for rule in self.rules if rule.name in rule_names]
        
        rule_results = []
        passed_count = 0
        failed_count = 0
        
        for rule in rules_to_apply:
            try:
                result = rule.validate(text)
                rule_results.append(result)
                
                if result["valid"]:
                    passed_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error applying rule {rule.name}: {str(e)}")
                rule_results.append({
                    "rule": rule.name,
                    "valid": False,
                    "message": f"Rule execution failed: {str(e)}",
                    "details": {"error": str(e)}
                })
                failed_count += 1
        
        overall_valid = failed_count == 0
        
        return {
            "valid": overall_valid,
            "message": f"Validation {'passed' if overall_valid else 'failed'}: "
                      f"{passed_count} passed, {failed_count} failed",
            "rules_passed": passed_count,
            "rules_failed": failed_count,
            "rule_results": rule_results
        }
    
    def validate_document_type(self, text: str, document_type: str) -> Dict[str, Any]:
        """Validate text for specific document type
        
        Args:
            text: Text to validate
            document_type: Type of document ('aadhaar', 'pan', 'passport', etc.)
        
        Returns:
            Document-specific validation results
        """
        # Create document-specific validator
        doc_validator = TextValidator()
        
        if document_type.lower() == "aadhaar":
            doc_validator.add_rule(AadhaarValidationRule())
            doc_validator.add_rule(DateValidationRule())
        elif document_type.lower() == "pan":
            doc_validator.add_rule(PANValidationRule())
        elif document_type.lower() in ["passport", "driving_license"]:
            doc_validator.add_rule(DateValidationRule())
            doc_validator.add_rule(PatternValidationRule(
                r'\b[A-Z]\d{7}\b', 
                "passport_number", 
                "Passport number format"
            ))
        
        return doc_validator.validate_text(text)
    
    def get_validation_summary(self, text: str) -> Dict[str, Any]:
        """Get a summary of validation results
        
        Args:
            text: Text to validate
        
        Returns:
            Validation summary
        """
        results = self.validate_text(text)
        
        # Extract key information
        summary = {
            "text_length": len(text.strip()),
            "overall_valid": results["valid"],
            "rules_applied": len(results["rule_results"]),
            "rules_passed": results["rules_passed"],
            "rules_failed": results["rules_failed"],
            "validation_score": results["rules_passed"] / max(len(results["rule_results"]), 1),
            "failed_rules": [r["rule"] for r in results["rule_results"] if not r["valid"]],
            "warnings": [r["message"] for r in results["rule_results"] if not r["valid"]]
        }
        
        return summary
    
    def get_available_rules(self) -> List[Dict[str, str]]:
        """Get list of available validation rules
        
        Returns:
            List of rule information dictionaries
        """
        return [
            {"name": rule.name, "description": rule.description}
            for rule in self.rules
        ]