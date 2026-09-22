# CNIC Verification System

A CNIC image verification application built with:

- Python
- FastAPI
- Streamlit
- EasyOCR
- OpenCV
- Supabase

## Pipeline

CNIC Image
↓
Streamlit
↓
FastAPI
↓
OpenCV
↓
EasyOCR
↓
CNIC Extraction
↓
CNIC Validation
↓
Supabase
↓
ACCEPTED / REJECTED

## Run Backend

python -m uvicorn Backend.main:app --reload

## Run Frontend

streamlit run Frontend/app.py  