import os
import json, re

from fastapi import FastAPI, UploadFile, Request, Form
# app = FastAPI()
# @app.get("/")
# def home():
#     return {"message": "FastAPI is running in Testing again....!"}

from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

#from models.classifier import classify_email, detect_multiple_requests
#from services.email_parser import extract_text_from_email
#from services.ocr_extractor import extract_text_from_pdf, extract_text_from_image
#from services.field_extractor import extract_fields
import email
from io import BytesIO

from pdfplumber import open as open_pdf
from PIL import Image
import pytesseract
from io import BytesIO
import re

from transformers import pipeline
from huggingface_hub import InferenceClient


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import io
from fastapi.responses import StreamingResponse
import hashlib

app = FastAPI()
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# LABELS = ["Adjustment", "Money Movement Inbound", "Funding Request",
#           "Loan Modification", "Closing Notice", "Fee Payment",
#           "Money Movement - Outbound", "AU Transfer"]

LABELS = [
    "Adjustment::None",
    "AU Transfer::None",
    "Loan Modification::None",
    "Funding Request::None",
    "Closing Notice::Reallocation Fees",
    "Closing Notice::Amendment Fees",
    "Closing Notice::Reallocation Principal",

    "Commitment Change::Decrease",
    "Commitment Change::Increase",
    "Commitment Change::Cashless Roll",
    "Fee Payment::Ongoing Fee",
    "Fee Payment::Letter of Credit Fee",

    "Money Movement Inbound::Principal",
    "Money Movement Inbound::Interest",
    "Money Movement Inbound::Principal + Interest",
    "Money Movement Inbound::Principal + Interest + Fee",
    "Money Movement Outbound::Time bound",
    "Money Movement Outbound::Foreign Currency"
]

@app.get("/")
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/classify", response_class=JSONResponse)
async def classify_email_view(request: Request, email_file: UploadFile):
    raw_email = await email_file.read()
    msg = email.message_from_bytes(raw_email)
    body, attachments = extract_text_from_email(msg)

    # OCR/Attachment Parsing
    attachment_texts = []
    for filename, content in attachments:
        if filename.endswith(".pdf"):
            attachment_texts.append(extract_text_from_pdf(content))
        elif filename.endswith((".png", ".jpg", ".jpeg")):
            attachment_texts.append(extract_text_from_image(content))

    full_text = body + "\n".join(attachment_texts)
    #return classify_email_local(full_text, LABELS)
    return classify_email_with_llama(full_text)

def classify_email_local(full_text, labels):
    # Classification and Field Extraction
    # print('full_text ',full_text)
    # print("Email Body ", full_text)

    print(repr(full_text))
    email_body = full_text.replace("\r\n", "\n").replace("\r", "\n")
    print(repr(email_body))
    full_text = repr(email_body)
    print("Final Email Body ", full_text)
    label, score, result = classify_email(full_text, labels)
    catAndSubCat = label.split('::')
    requestType = catAndSubCat[0]
    subRequestType = catAndSubCat[1]
    # label, score, result = classify_email_with_llama(full_text)
    # print("label: ", label, " score: ", score, " result: ", result)
    print(" result: ", result)
    # Display results
    for label, indScore in zip(result['labels'], result['scores']):
        print(f"{label}: {indScore:.4f}")
    fields = extract_fields(full_text, field_names)

    #requests, primary = detect_multiple_requests(full_text, LABELS)
    print("fields : ",fields)
    # print("requests--", requests)
    # print("primary--", primary)

    responseContent = {
        # "request": request,
        "requestType": requestType,
        "subRequestType": subRequestType,
        "score": round(score, 2),
        "fields": fields,
        #"multipleRequests": len(requests) > 0,
        #"requests": requests,
        "primary": requestType,
        "duplicate": "False"
    }
    return responseContent
field_names = [
    "deal_name",
    "monetary_amount",
    "expiration_date",
    "borrower_name",
    "loan_amount",
    "interest_rate",
    "loan_term",
    "maturity_date",
    "collateral",
    "lender_name",
    "loan_type",
    "closing_date",
    "payment_schedule",
    "guarantor",
    "loan_purpose",
    "fees",
    "covenants",
    "amortization_period",
    "escrow_requirements",
    "prepayment_penalty",
    "loan_status"
]

processed_emails = set()
# Initialize Hugging Face inference client
client = InferenceClient(model="mistralai/Mistral-7B-Instruct-v0.1",token="")



def classify_email_with_llama(email_body: str):
    """Classify email content using Mistral-7B"""
    print("Email Body ",email_body)

    print(repr(email_body))
    email_body = email_body.replace("\r\n", "\n").replace("\r", "\n")
    print(repr(email_body))
    email_body = repr(email_body)
    print("final body : ", email_body)
    #email_body = "Dear Loan Officer,\n\nI am writing to inquire about the current classification of my loan and to discuss potential reclassification options. Additionally, I would like to request an updated repayment schedule. Below are the details for your reference:\n\nLoan Account Number: 654321789\nBorrower Name: Jane Smith\nProperty Address: 456 Oak Avenue, Rivertown, TX 75001\n\nPlease confirm receipt and advise on the next steps. I look forward to your guidance on how to proceed with reclassification and repayment restructuring.\n\nThank you for your assistance."
    prompt = (
        "You are an AI Loan Agent that classifies emails into categories and sub-categories "
        "based on the given classification table. "
        "The main categories include 'Adjustment, 'Money Movement Inbound', 'Funding Request','Loan Modification', 'Closing Notice', 'Fee Payment', 'Money Movement - Outbound', 'AU Transfer', etc. "
        "with sub-categories under each. 'Reallocation Fees', 'Amendment Fees', 'Reallocation Principal', 'Cashless Roll', 'Decrease', 'Increase', 'Ongoing Fee', 'Letter of Credit Fee', 'Principal', 'Interest', 'Principal + Interest', 'Principal + Interest + Fee', 'Timebound', 'Foreign Currency'"
        f"Classify this email: {email_body}"
        "provide confidence score, , emotion score and detect for multiple requests, phishing email, duplicate email"
        "Output format first json in array and json need to have Category,Sub-Category,Confidence-score,Duplicate-Email, multiple-requests, phishing-email, emotion-score, intent and reasoning for classification in very short and crisp description"
    )

    # Call the model
    emailBodyLength = len(email_body)
    print(emailBodyLength)
    # response = client.text_generation(prompt, max_new_tokens=100)
    response = client.text_generation(prompt, max_new_tokens=emailBodyLength)
    print("response..Actual..  ", response)
    #cleaned_json_string = re.sub(r"(^```json|```$|^\.*|\.*$)", "", response.strip())
    cleaned_json_string = re.sub(r"^\.*|\.*$", "", response.strip())
    cleaned_json_string = re.sub(r"```json|```", "", cleaned_json_string).strip()
    cleaned_json_string = cleaned_json_string.replace('False', 'false').replace('True', 'true')
    print("cleaned_json_string --  ",cleaned_json_string)
    # Parse JSON

    data = json.loads(cleaned_json_string, strict=False)
    print("data....  ", data)
    first_json = ""
    multiReq = False
    if isinstance(data, list):
        first_json = data[0]
        if len(data) > 1:
            multiReq = True
    else:
        if re.search(r"emails", cleaned_json_string):
            first_json = data["emails"][0]
            if len(data["emails"]) > 1:
                multiReq = True
        else:
            first_json = data


    # Get the first JSON object


    print("first_json....  ",first_json)

    category = first_json["Category"]
    sub_category = first_json["Sub-Category"]
    confidence = first_json["Confidence-score"]
    duplicate_email = first_json["Duplicate-Email"]
    if multiReq:
        multiple_requests = "true"
    else:
        multiple_requests = "false"

    intent = first_json["intent"]
    responseContent = {
        # "request": request,
        "requestType": first_json["Category"],
        "subRequestType": first_json["Sub-Category"],
        "score": round(first_json["Confidence-score"], 2),
        "fields": {},
        "requests": [],
        "multipleRequests": multiple_requests,
        "primary": intent,
        "duplicate": duplicate_email,
        "phishingEmail": first_json["phishing-email"],
        "emotionScore": first_json["emotion-score"],
        "reasoning": first_json["reasoning"],
    }
    return responseContent
    # lines = response.split("\n")
    # classifications = []
    # score = []
    # for line in lines:
    #     print("line ", line)
    #     if "::" in line and "Confidence Score:" in line:
    #         print("line if", line)
    #         category_info, confidence = line.split(" | Confidence Score:")
    #         classifications.append({
    #             "category": category_info.split("::")[0].strip(),
    #             "sub_category": category_info.split("::")[1].strip(),
    #             "confidence_score": confidence.strip()
    #         })
    #         score.append(confidence.strip())
    # max_confidence = max(score) if score else 0.0
    # # Duplicate detection using email hash
    # email_hash = hashlib.md5(email_body.encode()).hexdigest()
    # is_duplicate = email_hash in processed_emails
    #
    # if not is_duplicate:
    #     processed_emails.add(email_hash)  # Store hash of processed email
    # return classifications, max_confidence, is_duplicate
    # return {
    #     "classifications": classifications,
    #     "confidence": max_confidence,
    #     "is_duplicate": is_duplicate
    #
    # }

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def classify_email(text, labels):
    #result = classifier(text, labels)
    result = classifier(text, labels, multi_label=True)


    best_label = result['labels'][0]
    score = result['scores'][0]
    return best_label, score, result

def detect_multiple_requests(text, labels):
    lines = text.split('\n')
    requests = []
    for line in lines:
        label, score, _ = classify_email(line, labels)
        if score > 0.8:
            requests.append((line.strip(), label, score))
    primary_request = max(requests, key=lambda x: x[2], default=None)
    return requests, primary_request

def extract_text_from_email(msg):
    body = ""
    attachments = []

    if msg.is_multipart():
        print("multipart")
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                text = part.get_payload(decode=True).decode(errors='ignore')
                print("text : :", text)
                body += text
            elif "attachment" in part.get("Content-Disposition", ""):
                filename = part.get_filename()
                content = part.get_payload(decode=True)
                attachments.append((filename, content))
    else:
        print("not multipart")
        text = msg.get_payload(decode=True).decode(errors='ignore')
        body += text

    return body, attachments

# def extract_text_from_email(msg):
#     body_lines = []
#     attachments = []
#
#     if msg.is_multipart():
#         for part in msg.walk():
#             content_type = part.get_content_type()
#             if content_type == "text/plain":
#                 text = part.get_payload(decode=True).decode(errors='ignore')
#                 body_lines.append(text)  # Store each text part as a separate line
#             elif part.get("Content-Disposition") and "attachment" in part.get("Content-Disposition", ""):
#                 filename = part.get_filename()
#                 content = part.get_payload(decode=True)
#                 attachments.append((filename, content))
#     else:
#         text = msg.get_payload(decode=True).decode(errors='ignore')
#         body_lines.append(text)
#
#     # Ensure all extracted text is joined with explicit newlines
#     body = "\n".join(body_lines)
#
#     return body, attachments

def extract_text_from_pdf(content):
    text = ""
    with open_pdf(BytesIO(content)) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def extract_text_from_image(content):
    img = Image.open(BytesIO(content))
    return pytesseract.image_to_string(img)

# field_patterns = {
#     "deal_name": r"Deal\s*Name\s*:\s*(.+)",
#     "monetary_amount": r"\$\s?[\d,]+(?:\.\d{2})?",
#     "expiration_date": r"\b(?:\d{1,2}/\d{1,2}/\d{2,4})\b"
# }

field_patterns = {
    "deal_name": r"(?i)Deal\s*Name\s*:\s*(.+)",
    "monetary_amount": r"(?i)\$\s?[\d,]+(?:\.\d{2})?",
    "expiration_date": r"(?i)\b(?:\d{1,2}/\d{1,2}/\d{2,4})\b",
    "borrower_name": r"(?i)Borrower\s*Name\s*:\s*(.+)",
    "loan_amount": r"(?i)Loan\s*Amount\s*:\s*\$\s?[\d,]+(?:\.\d{2})?",
    "interest_rate": r"(?i)Interest\s*Rate\s*:\s*(\d+\.?\d*)\%",
    "loan_term": r"(?i)Loan\s*Term\s*:\s*(\d+\s*(?:years?|months?))",
    "maturity_date": r"(?i)Maturity\s*Date\s*:\s*(\d{1,2}/\d{1,2}/\d{2,4})",
    "collateral": r"(?i)Collateral\s*:\s*(.+)",
    "lender_name": r"(?i)Lender\s*Name\s*:\s*(.+)",
    "loan_type": r"(?i)Loan\s*Type\s*:\s*(.+)",
    "closing_date": r"(?i)Closing\s*Date\s*:\s*(\d{1,2}/\d{1,2}/\d{2,4})",
    "payment_schedule": r"(?i)Payment\s*Schedule\s*:\s*(.+)",
    "guarantor": r"(?i)Guarantor\s*:\s*(.+)",
    "loan_purpose": r"(?i)Loan\s*Purpose\s*:\s*(.+)",
    "fees": r"(?i)Fees\s*:\s*\$\s?[\d,]+(?:\.\d{2})?",
    "covenants": r"(?i)Covenants\s*:\s*(.+)",
    "amortization_period": r"(?i)Amortization\s*Period\s*:\s*(\d+\s*(?:years?|months?))",
    "escrow_requirements": r"(?i)Escrow\s*Requirements\s*:\s*(.+)",
    "prepayment_penalty": r"(?i)Prepayment\s*Penalty\s*:\s*(.+)",
    "loan_status": r"(?i)Loan\s*Status\s*:\s*(.+)",
    "loan_number": r"(?i)Loan\s*Number\s*:\s*(\w+)",  # Alphanumeric loan number
    "origination_date": r"(?i)Origination\s*Date\s*:\s*(\d{1,2}/\d{1,2}/\d{2,4})",
    "repayment_type": r"(?i)Repayment\s*Type\s*:\s*(.+)",  # Fixed, variable, interest-only, etc.
    "disbursement_date": r"(?i)Disbursement\s*Date\s*:\s*(\d{1,2}/\d{1,2}/\d{2,4})",
    "funding_source": r"(?i)Funding\s*Source\s*:\s*(.+)",  # Bank, private lender, etc.
    "dscr": r"(?i)DSCR\s*\(Debt Service Coverage Ratio\)\s*:\s*(\d+\.?\d*)",
    "ltv": r"(?i)LTV\s*\(Loan-to-Value\)\s*:\s*(\d+\.?\d*)\%",
    "debt_yield": r"(?i)Debt\s*Yield\s*:\s*(\d+\.?\d*)\%",
    "principal_balance": r"(?i)Principal\s*Balance\s*:\s*\$\s?[\d,]+(?:\.\d{2})?",
    "remaining_term": r"(?i)Remaining\s*Term\s*:\s*(\d+\s*(?:years?|months?))",
    "interest_payment": r"(?i)Interest\s*Payment\s*:\s*\$\s?[\d,]+(?:\.\d{2})?",
    "principal_payment": r"(?i)Principal\s*Payment\s*:\s*\$\s?[\d,]+(?:\.\d{2})?",
    "balloon_payment": r"(?i)Balloon\s*Payment\s*:\s*\$\s?[\d,]+(?:\.\d{2})?",
    "late_fee": r"(?i)Late\s*Fee\s*:\s*\$\s?[\d,]+(?:\.\d{2})?",
    "prepayment_terms": r"(?i)Prepayment\s*Terms\s*:\s*(.+)"
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

@app.get("/addRequestType")
async def add_new_request(request: Request):
    return templates.TemplateResponse("add_new_request.html", {"request": request})

@app.get("/viewRequestTypes")
async def view_request(request: Request):
    return templates.TemplateResponse("view_request_types.html", {"request": request,
                                                                  "request_types": session_data["requests"]})
# Define request body model
# In-memory session storage
session_data = {"requests": []}  # Stores Request and SubRequests
@app.post("/save")
async def handle_form(
    requestType: str = Form(...),  # Form data for `requestType` (required)
    subRequestType: str = Form(None)  # Form data for `subRequestType` (optional)
):
    # Check if request type exists
    for req in session_data["requests"]:
        if req["requestType"] == requestType:
            req["subRequestType"].append(subRequestType)
            break
    else:
        # If request_type doesn't exist, add it
        session_data["requests"].append({
            "requestType": requestType,
            "subRequestType": [subRequestType]
        })
    return JSONResponse(content={"message": f"Request '{requestType}' with subrequest '{subRequestType}' saved successfully"})

# Define dates (X-axis)
dates = ["2025-03-23", "2025-03-24", "2025-03-25", "2025-03-26"]

# Define labels/categories (Y-axis)
categories = [
    "Adjustment",
    "Money Movement Inbound",
    "Funding Request",
    "Loan Modification",
    "Closing Notice",
    "Fee Payment",
    "Money Movement - Outbound",
    "AU Transfer"
]
@app.get("/dashboardChart")
def generate_chart():
    # Create a 2D NumPy array (Random sample values)
    data = np.random.randint(1, 100, size=(len(categories), len(dates)))

    # Convert to a Pandas DataFrame
    df = pd.DataFrame(data, index=categories, columns=dates)

    # Create the plot
    fig, ax = plt.subplots(figsize=(16, 9))  # Maximize figure size
    df.T.plot(kind="bar", ax=ax, width=0.8)

    # Formatting
    ax.set_xlabel("Date", fontsize=14, labelpad=10)
    ax.set_ylabel("Requests per day", fontsize=14, labelpad=10)
    ax.set_title("Category-wise Request Distribution Over Time", fontsize=16, pad=20)

    # Rotate and align X-axis labels
    ax.set_xticklabels(ax.get_xticklabels(), rotation=60, ha="right", fontsize=12)

    # Move legend outside
    ax.legend(title="Categories", bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=12)

    # Apply tight layout to ensure visibility
    plt.tight_layout()

    # Save plot to a bytes buffer with additional padding
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.2)
    buf.seek(0)
    plt.close()

    # Return image as response
    return StreamingResponse(buf, media_type="image/png", headers={"Cache-Control": "no-cache"})



