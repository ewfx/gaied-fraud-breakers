from pdfplumber import open as open_pdf
from PIL import Image
import pytesseract
from io import BytesIO

def extract_text_from_pdf(content):
    text = ""
    with open_pdf(BytesIO(content)) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def extract_text_from_image(content):
    img = Image.open(BytesIO(content))
    return pytesseract.image_to_string(img)
