import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def parse_prescription(raw_text: str) -> dict:
    """
    Takes raw OCR text → sends to Groq LLaMA → returns structured JSON
    """

    prompt = f"""
You are a medical data extraction AI. 
Extract structured information from this prescription text.

Return ONLY a valid JSON object. No explanation. No markdown. No extra text.
Just the raw JSON.

Extract these fields:
- doctor_name (string)
- doctor_qualification (string)  
- patient_name (string)
- patient_age (string)
- patient_gender (string)
- date (string)
- medicines (list of objects with these fields):
    - name (medicine name only, no brand)
    - dosage (eg: 500mg)
    - frequency (eg: twice daily, once daily)
    - duration (eg: 5 days, 1 week)
    - instructions (eg: after food, before sleep)
- additional_notes (string, any other instructions)

Rules:
- If any field is not found in the text, use null
- For medicines, extract every single medicine mentioned
- Clean up OCR errors if obvious (eg: "Paracetarn0l" → "Paracetamol")
- Do not add any information that is not in the text

Prescription text:
{raw_text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a precise medical data extraction assistant. Always return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,  # low temperature = more precise, less creative
        max_tokens=1000,
    )

    # Get the response text
    response_text = response.choices[0].message.content.strip()

    # Clean up if model accidentally added markdown code blocks
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]

    # Parse JSON
    try:
        parsed = json.loads(response_text)
        return parsed
    except json.JSONDecodeError as e:
        # If JSON parsing fails, return raw text in a dict
        return {
            "error": "Failed to parse LLM response as JSON",
            "raw_response": response_text
        }


def format_parsed_output(parsed: dict) -> str:
    """
    Takes parsed JSON dict → returns clean human readable summary
    Used for displaying in terminal or logs
    """
    if "error" in parsed:
        return f"Error: {parsed['error']}\nRaw: {parsed['raw_response']}"

    lines = []
    lines.append("=" * 50)
    lines.append("PARSED PRESCRIPTION")
    lines.append("=" * 50)

    lines.append(f"Doctor    : {parsed.get('doctor_name', 'N/A')}")
    lines.append(f"Patient   : {parsed.get('patient_name', 'N/A')}")
    lines.append(f"Age       : {parsed.get('patient_age', 'N/A')}")
    lines.append(f"Gender    : {parsed.get('patient_gender', 'N/A')}")
    lines.append(f"Date      : {parsed.get('date', 'N/A')}")
    lines.append("")
    lines.append("MEDICINES:")
    lines.append("-" * 50)

    medicines = parsed.get("medicines", [])
    for i, med in enumerate(medicines, 1):
        lines.append(f"{i}. {med.get('name', 'N/A')}")
        lines.append(f"   Dosage     : {med.get('dosage', 'N/A')}")
        lines.append(f"   Frequency  : {med.get('frequency', 'N/A')}")
        lines.append(f"   Duration   : {med.get('duration', 'N/A')}")
        lines.append(f"   Instructions: {med.get('instructions', 'N/A')}")
        lines.append("")

    if parsed.get("additional_notes"):
        lines.append(f"Notes: {parsed['additional_notes']}")

    lines.append("=" * 50)

    return "\n".join(lines)


# ── Quick test ────────────────────────────────────────
if __name__ == "__main__":

    # Simulate what Tesseract would give us
    sample_raw_text = """
    Dr. Ramesh Kumar MBBS, MD
    City Medical Center, Bengaluru

    Patient: Manu S        Age: 24     Gender: Male
    Date: 20/04/2026

    Rx:
    1. Paracetamol 500mg - 1 tablet twice daily x 5 days (after food)
    2. Azithromycin 250mg - 1 tablet once daily x 3 days (after food)
    3. Cetirizine 10mg - 1 tablet at night x 7 days (before sleep)

    Drink plenty of water. Rest for 2 days.
    Follow up after 1 week if no improvement.

    Dr. Ramesh Kumar
    """

    print("Testing LLM Parser with sample prescription text...\n")

    result = parse_prescription(sample_raw_text)
    print(format_parsed_output(result))

    print("\nRAW JSON OUTPUT:")
    print(json.dumps(result, indent=2))