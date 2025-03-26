# 🚀 Project Name

## 📌 Table of Contents
- [Introduction](#introduction)
- [Demo](#demo)
- [Inspiration](#inspiration)
- [What It Does](#what-it-does)
- [How We Built It](#how-we-built-it)
- [Challenges We Faced](#challenges-we-faced)
- [How to Run](#how-to-run)
- [Tech Stack](#tech-stack)
- [Team](#team)

---

## 🎯 Introduction
Gen AI-powered solution to extract, interpret, and classify loan servicing emails with contextual understanding, sub-category identification, and explainable reasoning.

## 🎥 Demo
📹 [Video Demo](#) attached in location [https://github.com/ewfx/gaied-fraud-breakers/tree/main/artifacts/demo](https://github.com/ewfx/gaied-fraud-breakers/blob/main/artifacts/demo/Demo.zip)

🖼️ Screenshots: Yes available in attached ppt in [https://github.com/ewfx/gaied-fraud-breakers/tree/main/artifacts/](https://github.com/ewfx/gaied-fraud-breakers/blob/main/artifacts/Email_Gatekeeper.pptx)

![Screenshot 1](link-to-image)

## 💡 Inspiration
The need to enhance efficiency in loan servicing workflows by automating email classification, reducing manual effort, improving accuracy in request handling, and ensuring timely responses inspired the problem-solving initiative. Traditional keyword-based systems struggle with context, intent recognition, and sub-category identification, making AI-powered solutions essential for better decision-making and transparency.

## ⚙️ What It Does
Intelligent email classification system using LLM
Context-based Data Extraction
Multi-Request Handling with Intent Detection
Priority-based Extraction
Duplicate Email Detection
Modular architecture for easy maintenance and scalability
![image](https://github.com/user-attachments/assets/cf091778-5515-40c4-8094-d03346b24aa2)


## 🛠️ How We Built It
Email or document extraction and parsing tokens
Earlier tried with Zero Shot Classification LLM, but rsults are not impressive, so used Sliding Window Attention LLM


## 🚧 Challenges We Faced
Identifying right and free LLM is difficult, unavailable of GPU in our personal machines, customizing and fine tuning the LLMs are major challenges. 

## 🏃 How to Run
1. Clone the repository  
   ```sh
   git clone [https://github.com/your-repo.git](https://github.com/ewfx/gaied-fraud-breakers/tree/main/code/src)
   ```
   Take src folder, create python project and place src the project
2. Install dependencies  
   ```sh
   or pip install -r requirements.txt (for Python), requirements.txt is available in [https://github.com/ewfx/gaied-fraud-breakers/tree/main](https://github.com/ewfx/gaied-fraud-breakers/blob/main/requirements.txt)
   ```
3. Run the project  
   ```sh
   use python uvicorn command
   ```
4. Create Access Token from Hugging Face and update in main.py

## 🏗️ Tech Stack
- 🔹 Frontend: HTML, Javascript, CSS, Ajax
- 🔹 Backend: Python, FastAPI, email, pytesseract, pdfplumber, Pillow, transformers, scikit-learn, uvicorn, jinja2, torch, python-multipart, pandas


## 👥 Team: **Fraud Breakers**
**Team Members**:
Vivek K Tripathi (Manager)
Vijaya Nagaraj SN(Architect)
Sree Deepthi Chintala (Development Lead)
Raghunatha R Devireddy (Development Lead)
Amit Agrawal (Quality & Service Virtualization Lead)

