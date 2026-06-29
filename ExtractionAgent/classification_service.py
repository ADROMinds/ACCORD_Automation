import os
import re
from pypdf import PdfReader, PdfWriter
from typing import TypedDict, Optional

class ClassificationResult(TypedDict):
    attachment_name: str
    is_acord: bool
    acord_type: Optional[str]
    is_blank: bool
    pages_in_order: bool
    is_valid: bool
    reason: Optional[str]
    cleaned_file_path: Optional[str]

def classify_and_clean(file_path: str, output_dir: str) -> ClassificationResult:
    """
    Classifies a PDF, checks for blank pages/order, and creates a cleaned version.
    """
    file_name = os.path.basename(file_path)
    result: ClassificationResult = {
        "attachment_name": file_name,
        "is_acord": False,
        "acord_type": None,
        "is_blank": True,
        "pages_in_order": True,
        "is_valid": False,
        "reason": None,
        "cleaned_file_path": None
    }

    try:
        reader = PdfReader(file_path)
        writer = PdfWriter()
        
        text_content = ""
        page_texts = []
        non_blank_pages = 0
        found_pages = []

        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            text_content += page_text
            page_texts.append(page_text.upper())
            
            # Check for "Page X"
            match = re.search(r"PAGE\s+(\d+)", page_text.upper())
            if match:
                found_pages.append(int(match.group(1)))

            # If page is not blank, add to writer
            if len(page_text.strip()) > 5: # Threshold for "not blank"
                writer.add_page(page)
                non_blank_pages += 1
                result["is_blank"] = False

        # ACORD Detection
        if "ACORD" in text_content.upper():
            result["is_acord"] = True
            if "CERTIFICATE OF LIABILITY INSURANCE" in text_content.upper():
                result["acord_type"] = "ACORD 25"
            elif "COMMERCIAL INSURANCE APPLICATION" in text_content.upper():
                result["acord_type"] = "ACORD 125"
            elif "EVIDENCE OF PROPERTY INSURANCE" in text_content.upper():
                result["acord_type"] = "ACORD 27"
            else:
                match = re.search(r"ACORD\s+(\d+)", text_content.upper())
                result["acord_type"] = f"ACORD {match.group(1)}" if match else "Unknown ACORD"

        # Page Order
        if found_pages and found_pages != sorted(found_pages):
            result["pages_in_order"] = False

        # Cleaning: Save the non-blank pages to a new file
        if not result["is_blank"]:
            cleaned_path = os.path.join(output_dir, f"cleaned_{file_name}")
            with open(cleaned_path, "wb") as f:
                writer.write(f)
            result["cleaned_file_path"] = cleaned_path

        # Overall Validity
        if not result["is_acord"]:
            result["reason"] = "Not an ACORD document"
        elif result["is_blank"]:
            result["reason"] = "Document is blank"
        elif not result["pages_in_order"]:
            result["reason"] = "Pages out of order"
        else:
            result["is_valid"] = True

    except Exception as e:
        result["is_valid"] = False
        result["reason"] = f"Error: {str(e)}"

    return result
