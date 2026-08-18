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
        
        # Build extraction prompt
        field_descriptions = []
        for field in fields:
            if isinstance(field, dict):
                name = field.get("name", "")
                desc = field.get("description", "")
                field_type = field.get("type", "string")
                required = field.get("required", False)
                field_descriptions.append(
                    f"- {name} ({field_type}{'*' if required else ''}): {desc}"
                )
            else:
                # Legacy simple field list
                field_descriptions.append(f"- {field}")
        
        field_list_str = "\n".join(field_descriptions)
        
        instructions = f"""Extract the following fields from the document text.

Document text:
{full_text}

Fields to extract:
{field_list_str}

For each field, find the value in the text above. Look for patterns like "Field Name: Value".

Return ONLY valid JSON in this exact format (no markdown, no extra text):
{{
  "field_name": {{"value": "extracted_value", "confidence": 0.95}},
  "another_field": {{"value": "another_value", "confidence": 0.85}}
}}

Examples:
- If text contains "Name: John Smith", extract {{"applicant_name": {{"value": "John Smith", "confidence": 0.95}}}}
- If text contains "Date: 15/03/1995", extract {{"date_filed": {{"value": "15/03/1995", "confidence": 0.95}}}}
- If a field is not found, use {{"field_name": {{"value": null, "confidence": 0.0}}}}

Rules:
- Extract exactly what appears in the document
- Confidence should be 0.9-1.0 if clearly found, 0.0 if not found
- Do not invent or guess values
- For dates, keep the format as shown in the document
- For addresses, include the full address as shown"""

        prompt = f"{instructions}"
        
        # Generate extraction using LLM
        try:
            # Use the LLM directly to generate response
            if hasattr(self.rag_engine, 'llm') and self.rag_engine.llm:
                raw_response = self.rag_engine.llm.generate_response(prompt, max_tokens=512)
            else:
                logger.error("No LLM available in RAG engine")
                raw_response = "{}"
            
            logger.info(f"LLM extraction response: {raw_response[:200]}...")
            parsed_fields = self._parse_llm_response(raw_response, fields)
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}", exc_info=True)
            parsed_fields = [
                {"field": self._get_field_name(f), "value": None, "confidence": 0.0}
                for f in fields
            ]
        
        # P4: Attach evidence to every extracted field
        extracted_with_evidence = []
        for field_data in parsed_fields:
            field_name = field_data["field"]
            value = field_data["value"]
            confidence = field_data["confidence"]
            
            # Find evidence for this field
            evidence = self.evidence_tracker.find_evidence(
                value, chunks, chunk_metadata, filename
            )
            
            # Get field metadata from schema
            field_info = self._get_field_info(fields, field_name)
            
            # Create extracted field with evidence
            extracted_field = create_extracted_field(
                field_name=field_name,
                value=value,
                confidence=confidence,
                evidence=evidence,
                field_type=field_info.get("type"),
                required=field_info.get("required")
            )
            
            extracted_with_evidence.append(extracted_field.to_dict())
        
        logger.info(f"Extracted {len(extracted_with_evidence)} fields from {document_type}")
        return extracted_with_evidence
    
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
