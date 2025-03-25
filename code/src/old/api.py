from fastapi import FastAPI, UploadFile, File, Form
from email_parser import parse_email_content
from extractor import extract_text_from_pdf, extract_text_from_image
from classifier import classify_email, detect_multiple_requests, prioritized_extraction
from utils import detect_duplicates, log_classification_reason
import email
from email.policy import default

app = FastAPI()

LABELS = ['Money Movement Inbound', 'Adjustment', 'Document Request']
REQUIRED_FIELDS = ['deal_name', 'monetary_amount', 'expiration_date']

@app.post("/analyze-email/")
async def analyze_email(email_file: UploadFile = File(...)):
    content = await email_file.read()
    msg = email.message_from_bytes(content, policy=default)
    body, attachments = parse_email_content(msg)

    attachment_texts = []
    for filename, content in attachments:
        if filename.endswith('.pdf'):
            attachment_texts.append(extract_text_from_pdf(content))
        elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            attachment_texts.append(extract_text_from_image(content))

    label, fields = prioritized_extraction(body, attachment_texts, LABELS, REQUIRED_FIELDS)
    requests, primary_request = detect_multiple_requests(body, LABELS)
    reason = log_classification_reason(body, classify_email(body, LABELS))
    duplicates = detect_duplicates([body] + attachment_texts)

    return {
        "subject": msg['subject'],
        "primary_request": primary_request,
        "fields_extracted": fields,
        "duplicates_detected": duplicates,
        "classification_reason": reason
    }
