import hashlib


def hash_text(text):
    return hashlib.md5(text.encode()).hexdigest()


def detect_duplicates(email_texts):
    seen_hashes = set()
    duplicates = []
    for text in email_texts:
        h = hash_text(text.strip())
        if h in seen_hashes:
            duplicates.append((text, h))
        else:
            seen_hashes.add(h)
    return duplicates


def log_classification_reason(email_text, classification_result):
    reason = f"Email classified as '{classification_result[0]}' with confidence {classification_result[1]:.2f}.\n"
    reason += f"Top alternatives: {classification_result[2]['labels'][:3]}."
    return reason