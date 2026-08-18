import json
import os
import re
from document.evidence import find_evidence

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "schemas")


def load_schema(document_type: str) -> list[str]:
    filename = document_type.lower().replace(" ", "_") + ".json"
    path = os.path.join(SCHEMA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)["fields"]


class FieldExtractor:
    def __init__(self, rag_engine):
        self.rag_engine = rag_engine

    def extract(self, chunks: list[str], chunk_metadata: list[dict], document_type: str, filename: str) -> list[dict]:
        fields = load_schema(document_type)
        if not fields:
            return []

        full_text = " ".join(chunks)[:4000]
        field_list = ", ".join(fields)
        instructions = (
            f"Extract the following fields: {field_list}.\n"
            f'Return ONLY valid JSON: {{"field_name": {{"value": "...", "confidence": 0.0}}, ...}}\n'
            f"If a field is not found, set value to null and confidence to 0."
        )
        prompt = f"Context:\n{full_text}\n\nQuestion: {instructions}\n\nAnswer:"

        raw = self.rag_engine._generate_llm_response(prompt, max_tokens=512)
        parsed_fields = self._parse(raw, fields)

        # P4: every field now carries source_document, page, and evidence_snippet
        return [
            {**f, **find_evidence(f["value"], chunks, chunk_metadata, filename)}
            for f in parsed_fields
        ]

    @staticmethod
    def _parse(raw_response: str, fields: list[str]) -> list[dict]:
        match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if not match:
            return [{"field": f, "value": None, "confidence": 0.0} for f in fields]
        try:
            parsed = json.loads(match.group())
        except json.JSONDecodeError:
            return [{"field": f, "value": None, "confidence": 0.0} for f in fields]
        return [
            {
                "field": f,
                "value": parsed.get(f, {}).get("value"),
                "confidence": parsed.get(f, {}).get("confidence", 0.0),
            }
            for f in fields
        ]