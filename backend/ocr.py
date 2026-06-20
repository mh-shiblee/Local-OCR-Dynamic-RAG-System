import fitz  # pymupdf
from pathlib import Path
from PIL import Image
from surya.ocr import run_ocr as surya_ocr
from surya.model.detection.model import load_model as load_det_model, load_processor as load_det_processor
from surya.model.recognition.model import load_model as load_rec_model
from surya.model.recognition.processor import load_processor as load_rec_processor

# Load models once at startup
det_processor = load_det_processor()
det_model = load_det_model()
rec_model = load_rec_model()
rec_processor = load_rec_processor()

LANGS = ["en", "bn"]  # English + Bangla


def pdf_to_images(pdf_path: str) -> list[Image.Image]:
    """Convert each PDF page to a PIL Image."""
    doc = fitz.open(pdf_path)
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    doc.close()
    return images


def run_ocr(file_path: str) -> str:
    """
    Run Surya OCR on a PDF or image file.
    Returns the full extracted text as a single string.
    """
    path = Path(file_path)

    if path.suffix.lower() == ".pdf":
        images = pdf_to_images(file_path)
    else:
        images = [Image.open(file_path).convert("RGB")]

    langs = [LANGS] * len(images)

    predictions = surya_ocr(
        images,
        langs,
        det_model,
        det_processor,
        rec_model,
        rec_processor
    )

    # Collect all text from all pages
    full_text = ""
    for page_num, prediction in enumerate(predictions):
        page_text = "\n".join([line.text for line in prediction.text_lines])
        full_text += f"\n--- Page {page_num + 1} ---\n{page_text}"

    return full_text.strip()
