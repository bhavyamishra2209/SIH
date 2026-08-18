"""
Enhanced field extraction module with schema-based extraction.
P3 requirement: Config-based JSON schemas per document type.
P4 requirement: Evidence tracking for every extracted field.
"""

import json
import os
import re
import logging
from typing import List, Dict, Any, Optional

from document.evidence_tracker import EvidenceTracker, create_extracted_field, Evidence

logger = logging.getLogger(__name__)

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "schemas")


def load_schema(document_type: str) -> Dict[str, Any]:
    """
    Load JSON schema for a document type.
    
    Args:
        document_type: Type of document (e.g., "Application", "Identity Proof")
        
    Returns:
        Schema dictionary with fields and metadata
    """
    # Normalize document type name to filename
    filename = document_type.lower().replace(" ", "_") + ".json"
    path = os.path.join(SCHEMA_DIR, filename)
    
    if not os.path.exists(path):
        logger.warning(f"Schema not found for document type: {document_type}")
        return {"fields": []}
    
    try:
        with open(path, 'r') as f:
            schema = json.load(f)
        return schema
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse schema {filename}: {e}")
        return {"fields": []}


class FieldExtractor:
    """
    Schema-based field extraction with LLM and evidence tracking.
    """
    
    def __init__(self, rag_engine):
        """
        Initialize field extractor.
        
        Args:
            rag_engine: RAG engine instance with LLM access
        """
        self.rag_engine = rag_engine
        self.evidence_tracker = EvidenceTracker()
    
    def extract(
        self, 
        chunks: List[str], 
        chunk_metadata: List[Dict[str, Any]], 
        document_type: str, 
        filename: str
    ) -> List[Dict[str, Any]]:
        """
        Extract structured fields from document chunks using schema.
        
        Args:
            chunks: List of text chunks from document
            chunk_metadata: Metadata for each chunk
            document_type: Type of document
            filename: Source filename
            
        Returns:
            List of extracted fields with evidence
        """
        # Load schema for document type
        schema = load_schema(document_type)
        fields = schema.get("fields", [])
        
        if not fields:
            logger.warning(f"No fields defined for document type: {document_type}")
            return []
        
        # Prepare text for extraction (limit to avoid token limits)
        full_text = " ".join(chunks)[:4000]
        
        # Use regex-based extraction instead of LLM for better reliability
        extracted_fields = []
        
        for field in fields:
            field_name = self._get_field_name(field)
            field_info = self._get_field_info(fields, field_name)
            
            # Try to extract value using pattern matching
            value, confidence = self._extract_field_value(field_name, full_text)
            
            # Find evidence for this field
            evidence = self.evidence_tracker.find_evidence(
                value, chunks, chunk_metadata, filename
            )
            
            # Create extracted field with evidence
            extracted_field = create_extracted_field(
                field_name=field_name,
                value=value,
                confidence=confidence,
                evidence=evidence,
                field_type=field_info.get("type"),
                required=field_info.get("required")
            )
            
            extracted_fields.append(extracted_field.to_dict())
        
        logger.info(f"Extracted {len(extracted_fields)} fields from {document_type}")
        return extracted_fields
    
    def _extract_field_value(self, field_name: str, text: str) -> tuple:
        """
        Extract field value using pattern matching.
        
        Args:
            field_name: Name of field to extract
            text: Document text
            
        Returns:
            Tuple of (value, confidence)
        """
        # Define field patterns - map field names to search patterns
        field_patterns = {
            'applicant_name': [
                r'name\s*[:=]\s*([^\n]+?)(?:\s+date|$)',
                r'applicant\s+name\s*[:=]\s*([^\n]+?)(?:\s+date|$)',
            ],
            'application_number': [
                r'application\s+(?:no|number|#)\s*[:=]?\s*([A-Z0-9\-]+)',
                r'reference\s+(?:no|number)\s*[:=]?\s*([A-Z0-9\-]+)',
            ],
            'date_filed': [
                r'application\s+date\s*[:=]\s*([0-9/\-]+)',
                r'date\s+filed\s*[:=]\s*([0-9/\-]+)',
                r'filed\s+on\s*[:=]?\s*([0-9/\-]+)',
            ],
            'purpose': [
                r'purpose\s*[:=]\s*([^\n]+?)(?:\s+[A-Z][a-z]+:|$)',
                r'reason\s*[:=]\s*([^\n]+?)(?:\s+[A-Z][a-z]+:|$)',
            ],
            'applicant_address': [
                r'address\s*[:=]\s*([^\n]+?)(?:\s+license|$)',
                r'residential\s+address\s*[:=]\s*([^\n]+?)(?:\s+license|$)',
            ],
            'contact_number': [
                r'phone\s*[:=]?\s*([0-9\-\(\)\s]+)',
                r'contact\s+number\s*[:=]?\s*([0-9\-\(\)\s]+)',
                r'mobile\s*[:=]?\s*([0-9\-\(\)\s]+)',
            ],
            'email': [
                r'email\s*[:=]?\s*([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
            ],
            'department': [
                r'department\s*[:=]\s*([^\n]+?)(?:\s+[A-Z]|$)',
            ],
        }
        
        # Try patterns for this field
        patterns = field_patterns.get(field_name, [])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Clean up value
                value = re.sub(r'\s+', ' ', value)  # Normalize spaces
                value = value.rstrip(',.')  # Remove trailing punctuation
                
                if value:
                    logger.info(f"Extracted {field_name}: {value}")
                    return value, 0.9
        
        # Not found
        logger.debug(f"Field {field_name} not found in text")
        return None, 0.0
    
    @staticmethod
    def _get_field_name(field: Any) -> str:
        """Extract field name from field definition."""
        if isinstance(field, dict):
            return field.get("name", str(field))
        return str(field)
    
    @staticmethod
    def _get_field_info(fields: List[Any], field_name: str) -> Dict[str, Any]:
        """Get field metadata from schema."""
        for field in fields:
            if isinstance(field, dict) and field.get("name") == field_name:
                return field
        return {}
    
    def _parse_llm_response(
        self, 
        raw_response: str, 
        fields: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Parse LLM response to extract field values and confidence.
        
        Args:
            raw_response: Raw LLM output
            fields: List of field definitions from schema
            
        Returns:
            List of parsed fields with value and confidence
        """
        # Try to find JSON in the response
        match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if not match:
            logger.warning("No JSON found in LLM response")
            return [
                {
                    "field": self._get_field_name(f), 
                    "value": None, 
                    "confidence": 0.0
                } 
                for f in fields
            ]
        
        try:
            parsed = json.loads(match.group())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM: {e}")
            return [
                {
                    "field": self._get_field_name(f), 
                    "value": None, 
                    "confidence": 0.0
                } 
                for f in fields
            ]
        
        # Extract field values
        results = []
        for field in fields:
            field_name = self._get_field_name(field)
            field_data = parsed.get(field_name, {})
            
            # Handle both dict format and direct value
            if isinstance(field_data, dict):
                value = field_data.get("value")
                confidence = field_data.get("confidence", 0.0)
            else:
                value = field_data
                confidence = 0.7 if value is not None else 0.0
            
            results.append({
                "field": field_name,
                "value": value,
                "confidence": float(confidence) if confidence is not None else 0.0
            })
        
        return results
