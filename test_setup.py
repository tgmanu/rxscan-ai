import pytesseract
import cv2
import groq
import streamlit
import fastapi
from dotenv import load_dotenv
import os

load_dotenv()

pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_PATH")

groq_key = os.getenv("GROQ_API_KEY")
tesseract_path = os.getenv("TESSERACT_PATH")

print("✅ All libraries imported successfully")
print(f"✅ Groq API Key loaded: {groq_key[:10] if groq_key else '❌ NOT FOUND - check .env file'}")
print(f"✅ Tesseract path: {tesseract_path if tesseract_path else '❌ NOT FOUND - check .env file'}")

try:
    version = pytesseract.get_tesseract_version()
    print(f"✅ Tesseract version: {version}")
except Exception as e:
    print(f"❌ Tesseract error: {e}")