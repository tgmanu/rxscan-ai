import cv2
import numpy as np
import pytesseract
from PIL import Image
import os
from dotenv import load_dotenv

load_dotenv()

tesseract_path = os.getenv("TESSERACT_PATH")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path


def preprocess_image(image_path: str) -> np.ndarray:
    """
    Takes raw image path, cleans it for better OCR accuracy.
    Steps: grayscale → denoise → threshold → deskew
    """
    # Read image
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError(f"Could not read image at path: {image_path}")

    # Step 1: Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Step 2: Remove noise
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # Step 3: Thresholding (converts to pure black and white)
    # This makes text stand out clearly
    _, threshold = cv2.threshold(
        denoised, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # Step 4: Dilation to make text thicker and clearer
    kernel = np.ones((1, 1), np.uint8)
    processed = cv2.dilate(threshold, kernel, iterations=1)

    return processed


def extract_text_from_image(image_path: str) -> str:
    """
    Main function: takes image path → returns extracted raw text
    """
    # Preprocess the image first
    processed_img = preprocess_image(image_path)

    # Convert numpy array back to PIL Image for tesseract
    pil_image = Image.fromarray(processed_img)

    # Tesseract config:
    # --oem 3 = best OCR engine mode
    # --psm 6 = assume a uniform block of text
    custom_config = r'--oem 3 --psm 6'

    # Extract text
    raw_text = pytesseract.image_to_string(pil_image, config=custom_config)

    return raw_text.strip()


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Converts PDF pages to images first, then extracts text from each page
    """
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise ImportError("pdf2image not installed. Run: pip install pdf2image")

    # Convert PDF pages to images
    pages = convert_from_path(pdf_path, dpi=300)

    all_text = []

    for i, page in enumerate(pages):
        # Save each page temporarily
        temp_path = f"temp_page_{i}.png"
        page.save(temp_path, "PNG")

        # Extract text from that page
        text = extract_text_from_image(temp_path)
        all_text.append(text)

        # Clean up temp file
        os.remove(temp_path)

    return "\n\n".join(all_text)


def extract_text(file_path: str) -> str:
    """
    Smart router: detects if file is image or PDF and calls right function
    This is what main.py will call
    """
    extension = os.path.splitext(file_path)[1].lower()

    if extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        return extract_text_from_image(file_path)

    elif extension == '.pdf':
        return extract_text_from_pdf(file_path)

    else:
        raise ValueError(f"Unsupported file type: {extension}. Use jpg, png, or pdf.")


# ── Quick test (run this file directly to test) ──────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ocr_engine.py <path_to_image>")
        print("\nRunning with a generated test image instead...\n")

        # Create a simple test image with text
        test_img = np.ones((200, 600), dtype=np.uint8) * 255
        cv2.putText(test_img, "Patient: Manu S", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(test_img, "Medicine: Paracetamol 500mg", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(test_img, "Dosage: Twice daily x 5 days", (10, 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

        test_path = "test_prescription.png"
        cv2.imwrite(test_path, test_img)
        print(f"Created test image: {test_path}")

        result = extract_text(test_path)
        os.remove(test_path)

    else:
        result = extract_text(sys.argv[1])

    print("=" * 50)
    print("EXTRACTED TEXT:")
    print("=" * 50)
    print(result)
    print("=" * 50)