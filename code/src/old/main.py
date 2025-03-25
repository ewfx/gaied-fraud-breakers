from email_parser import fetch_emails, parse_email_content
from extractor import extract_text_from_pdf, extract_text_from_image
from classifier import classify_email, detect_multiple_requests, prioritized_extraction
from utils import detect_duplicates, log_classification_reason

# Config
IMAP_HOST = 'imap.example.com'
USERNAME = 'user@example.com'
PASSWORD = 'password'
LABELS = ['Money Movement Inbound', 'Adjustment', 'Document Request']
REQUIRED_FIELDS = ['deal_name', 'monetary_amount', 'expiration_date']

if __name__ == "__main__":
    emails = fetch_emails(IMAP_HOST, USERNAME, PASSWORD)
    for msg in emails:
        body, attachments = parse_email_content(msg)

        attachment_texts = []
        for filename, content in attachments:
            if filename.endswith('.pdf'):
                attachment_texts.append(extract_text_from_pdf(content))
            elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                attachment_texts.append(extract_text_from_image(content))

        # Classification and Extraction
        label, fields = prioritized_extraction(body, attachment_texts, LABELS, REQUIRED_FIELDS)
        requests, primary_request = detect_multiple_requests(body, LABELS)
        reason = log_classification_reason(body, classify_email(body, LABELS))

        # Duplicate Detection
        duplicates = detect_duplicates([body] + attachment_texts)

        # Output Results
        print(f"Email Subject: {msg['subject']}")
        print(f"Primary Request: {primary_request}")
        print(f"Fields Extracted: {fields}")
        print(f"Duplicates Detected: {duplicates}")
        print(f"Classification Reason: {reason}\n\n")