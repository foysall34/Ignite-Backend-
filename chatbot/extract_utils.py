import docx
import PyPDF2
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

def extract_text_from_file(path):
    print("======================================")
    print("🔍 DEBUGGING EXTRACTOR STARTED")
    print(f"📄 File Path: {path}")
    print("======================================")

    # ------------------------------
    # 1️⃣ PDF Extract
    # ------------------------------
    if path.endswith(".pdf"):
        text = ""
        print("📁 PDF detected. Trying PyPDF2 extract...")

        try:
            reader = PyPDF2.PdfReader(path)
            print(f"📄 Total PDF Pages: {len(reader.pages)}")

            for i, page in enumerate(reader.pages):
                print(f"➡️ Extracting Page {i+1} with PyPDF2...")
                extracted = page.extract_text()
                print(f"    ↳ Extracted Length: {len(extracted) if extracted else 0}")

                if extracted:
                    text += extracted

        except Exception as e:
            print(f"❌ PyPDF2 ERROR: {e}")

        print(f"📌 PyPDF2 Total Extracted Characters: {len(text)}")

        # ------------------------------
        # 2️⃣ OCR fallback
        # ------------------------------
        if len(text.strip()) == 0:
            print("⚠️ No text found. Running OCR fallback...")
            try:
                print("⏳ Converting PDF → Images using pdf2image...")
                images = convert_from_path(path, poppler_path="/usr/bin")
                print(f"🖼️ Total Images Generated: {len(images)}")
            except Exception as e:
                print(f"❌ pdf2image ERROR: {e}")
                return ""

            print("🔍 Running OCR on each image...")

            for idx, img in enumerate(images):
                print(f"➡️ OCR on image {idx+1}/{len(images)}...")
                try:
                    ocr_text = pytesseract.image_to_string(img)
                    print(f"    ↳ OCR Extracted Characters: {len(ocr_text)}")
                    text += ocr_text
                except Exception as e:
                    print(f"❌ OCR ERROR on page {idx+1}: {e}")

        print(f"📌 FINAL Extracted Characters (PDF): {len(text)}")
        print("======================================")
        return text

    # ------------------------------
    # DOCX
    # ------------------------------
    if path.endswith(".docx"):
        print("📁 DOCX detected.")
        try:
            doc = docx.Document(path)
            text = "\n".join([p.text for p in doc.paragraphs])
            print(f"📌 Extracted DOCX Characters: {len(text)}")
        except Exception as e:
            print(f"❌ DOCX ERROR: {e}")
            text = ""
        print("======================================")
        return text

    # ------------------------------
    # TXT
    # ------------------------------
    if path.endswith(".txt"):
        print("📁 TXT detected.")
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            print(f"📌 Extracted TXT Characters: {len(text)}")
        except Exception as e:
            print(f"❌ TXT ERROR: {e}")
            text = ""
        print("======================================")
        return text

    # Unknown type
    print("⚠️ Unsupported file type.")
    print("======================================")
    return ""
