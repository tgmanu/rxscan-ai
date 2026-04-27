import os
import shutil
from pathlib import Path

# ── Indian → US FDA drug name translations ──────────────
INDIAN_TO_FDA_NAMES = {
    "paracetamol": "acetaminophen",
    "salbutamol": "albuterol",
    "pethidine": "meperidine",
    "adrenaline": "epinephrine",
    "noradrenaline": "norepinephrine",
    "frusemide": "furosemide",
    "lignocaine": "lidocaine",
    "metronidazole": "metronidazole",
    "amoxycillin": "amoxicillin",
    "cephalexin": "cefalexin",
    "ibuprofen": "ibuprofen",
    "omeprazole": "omeprazole",
    "pantoprazole": "pantoprazole",
    "atorvastatin": "atorvastatin",
    "metformin": "metformin",
}

# ── Allowed file types ───────────────────────────────────
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".pdf"}

# ── Max file size: 10MB ──────────────────────────────────
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def translate_medicine_name(name: str) -> str:
    """
    Converts Indian drug names to US FDA names for better API results
    Returns original name if no translation found
    """
    if not name:
        return name
    translated = INDIAN_TO_FDA_NAMES.get(name.lower().strip())
    return translated if translated else name


def validate_file(file_path: str) -> dict:
    """
    Validates uploaded file — checks type and size
    Returns dict with is_valid flag and message
    """
    path = Path(file_path)

    # Check file exists
    if not path.exists():
        return {
            "is_valid": False,
            "message": f"File not found: {file_path}"
        }

    # Check file extension
    extension = path.suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        return {
            "is_valid": False,
            "message": f"Invalid file type '{extension}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        }

    # Check file size
    file_size = path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        return {
            "is_valid": False,
            "message": f"File too large ({size_mb:.1f}MB). Max allowed: {MAX_FILE_SIZE_MB}MB"
        }

    # Check file is not empty
    if file_size == 0:
        return {
            "is_valid": False,
            "message": "File is empty"
        }

    return {
        "is_valid": True,
        "message": "File is valid",
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "extension": extension
    }


def save_upload(file_path: str, destination_dir: str = "uploads") -> str:
    """
    Saves uploaded file to a destination directory
    Returns the new file path
    """
    os.makedirs(destination_dir, exist_ok=True)
    filename = Path(file_path).name
    destination = os.path.join(destination_dir, filename)
    shutil.copy2(file_path, destination)
    return destination


def cleanup_file(file_path: str) -> None:
    """
    Deletes a temp file after processing
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Warning: Could not delete temp file {file_path}: {e}")


def format_file_size(size_bytes: int) -> str:
    """
    Converts bytes to human readable format
    """
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f}KB"
    else:
        return f"{size_bytes/(1024*1024):.1f}MB"


def get_supported_formats() -> list:
    """
    Returns list of supported file formats for UI display
    """
    return [ext.replace(".", "").upper() for ext in ALLOWED_EXTENSIONS]


# ── Quick test ───────────────────────────────────────────
if __name__ == "__main__":

    print("Testing name translation...")
    test_names = ["Paracetamol", "Salbutamol", "Azithromycin", "Ibuprofen", "RandomDrug"]
    for name in test_names:
        translated = translate_medicine_name(name)
        status = "→ translated" if translated != name else "→ no translation needed"
        print(f"  {name:20} {status:25} = {translated}")

    print("\nTesting file validation...")
    # Create a dummy test file
    test_file = "test_dummy.jpg"
    with open(test_file, "w") as f:
        f.write("dummy content")

    result = validate_file(test_file)
    print(f"  Dummy jpg file: {result}")

    result = validate_file("nonexistent.jpg")
    print(f"  Nonexistent file: {result}")

    result = validate_file("test_dummy.exe")
    print(f"  Invalid extension: {result}")

    cleanup_file(test_file)

    print("\nSupported formats:", get_supported_formats())