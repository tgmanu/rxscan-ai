# 💊 RxScan AI — Prescription Medicine Extractor

> Upload a prescription image → Extract medicines → Get real FDA drug info instantly

## 🚀 Live Demo
[Add Streamlit Cloud link after deployment]

## 🎯 What it does
RxScan AI extracts structured medicine data from prescription images using:
- **OCR** (OpenCV + Tesseract) to extract raw text
- **LLM** (Groq LLaMA 3.3 70B) to parse medicines into structured JSON
- **OpenFDA API** to fetch real drug warnings, side effects & interactions

## 🏗️ Architecture
Prescription Image
↓
OpenCV (preprocessing) + Tesseract (OCR)
↓
Groq LLaMA 3.3 70B (structured parsing)
↓
OpenFDA API (drug enrichment)
↓
FastAPI (backend) + Streamlit (frontend)

## 🛠️ Tech Stack
| Layer | Technology |
|---|---|
| Image Processing | OpenCV |
| OCR Engine | Tesseract 5.5 |
| LLM Parsing | Groq API (LLaMA 3.3 70B) |
| Drug Database | OpenFDA Public API |
| Backend | FastAPI |
| Frontend | Streamlit |

## ⚡ Key Features
- Supports JPG, PNG, PDF prescriptions
- Auto-translates Indian drug names to FDA names (Paracetamol → Acetaminophen)
- Real FDA warnings, side effects, drug interactions
- Downloadable JSON report
- Clean REST API with auto-generated docs

## 🚀 Run Locally

### 1. Clone the repo
```
git clone https://github.com/YOUR_USERNAME/rxscan-ai.git
cd rxscan-ai
```

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Set up .env
GROQ_API_KEY=your_groq_api_key
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe

### 4. Run backend
```
uvicorn backend.main:app --reload --port 8000
```

### 5. Run frontend
```
streamlit run frontend/app.py
```

## 📁 Project Structure
rxscan-ai/
├── backend/
│   ├── main.py          # FastAPI server
│   ├── ocr_engine.py    # OpenCV + Tesseract
│   ├── llm_parser.py    # Groq LLaMA parsing
│   ├── fda_lookup.py    # OpenFDA API
│   └── utils.py         # Helpers + name translation
├── frontend/
│   └── app.py           # Streamlit UI
└── requirements.txt
