import sys  
import os
sys.path.append(os.path.dirname(__file__))

import shutil
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from ocr_engine import extract_text
from llm_parser import parse_prescription
from fda_lookup import lookup_all_medicines
from utils import validate_file, translate_medicine_name, cleanup_file

load_dotenv()

# ── Initialize FastAPI app ───────────────────────────────
app = FastAPI(
    title="RxScan AI",
    description="Prescription Medicine Text Extractor powered by OCR + LLM + FDA",
    version="1.0.0"
)

# ── CORS middleware ──────────────────────────────────────
# Allows Streamlit frontend to talk to this FastAPI backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Temp upload directory ────────────────────────────────
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Routes ───────────────────────────────────────────────

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "app": "RxScan AI",
        "version": "1.0.0",
        "message": "Prescription extraction API is live"
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "groq_key_loaded": bool(os.getenv("GROQ_API_KEY")),
        "tesseract_path": os.getenv("TESSERACT_PATH"),
        "upload_dir_exists": os.path.exists(UPLOAD_DIR)
    }


@app.post("/extract")
async def extract_prescription(file: UploadFile = File(...)):
    """
    Main endpoint — full pipeline:
    Upload image/PDF → OCR → LLM parse → FDA lookup → return JSON
    """

    # Step 1: Save uploaded file temporarily
    extension = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{extension}"
    temp_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Step 2: Validate file
        validation = validate_file(temp_path)
        if not validation["is_valid"]:
            raise HTTPException(status_code=400, detail=validation["message"])

        # Step 3: OCR — extract raw text
        print(f"\n[1/3] Running OCR on {file.filename}...")
        raw_text = extract_text(temp_path)

        if not raw_text.strip():
            raise HTTPException(
                status_code=422,
                detail="Could not extract any text from the image. Please upload a clearer image."
            )

        print(f"      Raw text extracted ({len(raw_text)} characters)")

        # Step 4: LLM — parse raw text into structured JSON
        print(f"[2/3] Parsing with Groq LLaMA...")
        parsed = parse_prescription(raw_text)

        if "error" in parsed:
            raise HTTPException(
                status_code=500,
                detail=f"LLM parsing failed: {parsed['error']}"
            )

        print(f"      Found {len(parsed.get('medicines', []))} medicines")

        # Step 5: FDA lookup — enrich each medicine
        print(f"[3/3] Looking up medicines in FDA database...")
        medicines = parsed.get("medicines", [])

        # Translate Indian names before FDA lookup
        for med in medicines:
            med["name"] = translate_medicine_name(med.get("name", ""))

        enriched_medicines = lookup_all_medicines(medicines)
        print(f"      FDA lookup complete")

        # Step 6: Build final response
        response = {
            "status": "success",
            "filename": file.filename,
            "raw_text": raw_text,
            "prescription": {
                "doctor_name": parsed.get("doctor_name"),
                "doctor_qualification": parsed.get("doctor_qualification"),
                "patient_name": parsed.get("patient_name"),
                "patient_age": parsed.get("patient_age"),
                "patient_gender": parsed.get("patient_gender"),
                "date": parsed.get("date"),
                "additional_notes": parsed.get("additional_notes"),
            },
            "medicines": enriched_medicines,
            "total_medicines": len(enriched_medicines),
        }

        return response

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )

    finally:
        # Always clean up temp file
        cleanup_file(temp_path)


@app.get("/supported-formats")
def supported_formats():
    """Returns list of supported file formats"""
    return {
        "formats": ["JPG", "JPEG", "PNG", "BMP", "TIFF", "PDF"],
        "max_size_mb": 10
    }