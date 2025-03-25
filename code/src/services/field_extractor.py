import re

field_patterns = {
    "deal_name": r"Deal\s*Name\s*:\s*(.+)",
    "monetary_amount": r"\$\s?[\d,]+(?:\.\d{2})?",
    "expiration_date": r"\b(?:\d{1,2}/\d{1,2}/\d{2,4})\b"
}

def extract_fields(text, required_fields):
    extracted = {}
    for field in required_fields:
        pattern = field_patterns.get(field)
        if pattern:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted[field] = match.group(0)
    return extracted
