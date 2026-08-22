def find_evidence(value, chunks: list[str], chunk_metadata: list[dict], filename: str) -> dict:
    """
    Given an extracted field value, locate which source chunk it actually
    came from and build a standard evidence record.
    
    ISSUE 2 FIX: Uses fuzzy matching to handle OCR errors and LLM reformatting.
    Falls back from exact match → fuzzy match → default evidence.
    """
    if not value:
        return {"source_document": filename, "page": None, "evidence_snippet": None}

    from rapidfuzz import fuzz
    
    value_str = str(value).strip()
    
    # ATTEMPT 1: Exact substring match (fastest, most accurate when it works)
    for text, meta in zip(chunks, chunk_metadata):
        idx = text.find(value_str)
        if idx != -1:
            start, end = max(0, idx - 60), min(len(text), idx + len(value_str) + 60)
            return {
                "source_document": filename,
                "page": meta.get("page", "unknown"),
                "evidence_snippet": text[start:end].strip(),
                "confidence": 1.0,  # Exact match = high confidence
            }
    
    # ATTEMPT 2: Fuzzy matching (handles OCR errors, case differences, date formatting)
    # Use partial_ratio to find best substring match even if formats differ
    best_match = None
    best_score = 0
    best_chunk_idx = -1
    
    for i, (text, meta) in enumerate(zip(chunks, chunk_metadata)):
        # Split text into overlapping windows roughly the size of value_str
        # to find the best local match
        window_size = max(len(value_str) + 20, 100)
        for start in range(0, len(text), window_size // 2):
            window = text[start:start + window_size]
            score = fuzz.partial_ratio(value_str.lower(), window.lower())
            if score > best_score:
                best_score = score
                best_match = window
                best_chunk_idx = i
    
    # If fuzzy match is strong enough (≥80%), use it
    if best_score >= 80 and best_match:
        return {
            "source_document": filename,
            "page": chunk_metadata[best_chunk_idx].get("page", "unknown"),
            "evidence_snippet": best_match.strip(),
            "confidence": best_score / 100.0,  # Normalize to 0-1
            "match_type": "fuzzy",
        }
    
    # ATTEMPT 3: Fallback - no good match found
    # Return first chunk as fallback context (better than nothing)
    if chunks and chunk_metadata:
        fallback_snippet = chunks[0][:200].strip() + "..."
        return {
            "source_document": filename,
            "page": chunk_metadata[0].get("page", "unknown"),
            "evidence_snippet": f"[No exact match found] {fallback_snippet}",
            "confidence": 0.0,
            "match_type": "fallback",
        }
    
    # ATTEMPT 4: Complete failure - no chunks at all
    return {
        "source_document": filename,
        "page": "unknown",
        "evidence_snippet": "Value not found in document",
        "confidence": 0.0,
        "match_type": "none",
    }