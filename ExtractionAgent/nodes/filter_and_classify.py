import os
import logging
import requests
from typing import Dict, Any
from urllib.parse import urlencode
from state import StateModel, ProcessingResult

logger = logging.getLogger(__name__)

# ── Credentials & Config ─────────────────────────────────────────────────────
CLIENT_ID     = "29e4161e-9863-44a6-b5dc-a0e7da356ac7"
CLIENT_SECRET = "XMloS2Mr_HoaXSxAf8_7U9W*OUqA5BZAYNNDb9A2#d%VK@^LI7f0RQ#xU7Ky9meu"
ORG           = "hackathon26_585"
TENANT        = "DefaultTenant"
FOLDER_ID     = "3084015"
BUCKET_ID     = "218383"
ORCH_URL      = f"https://staging.uipath.com/{ORG}/{TENANT}/orchestrator_"

# ── ACORD Types to detect ─────────────────────────────────────────────────────
ACORD_TYPES = {
    "ACORD 25":  ["certificate of liability", "acord 25", "acord25"],
    "ACORD 125": ["commercial insurance", "acord 125", "acord125", "applicant information"],
    "ACORD 126": ["commercial general liability", "acord 126", "acord126", "occurrence"],
    "ACORD 140": ["property", "acord 140", "acord140", "building"],
    "ACORD 75":  ["acord 75", "acord75", "surplus lines"],
}


def get_token() -> str:
    payload = urlencode({
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope":         "OR.Jobs OR.Execution OR.Folders OR.Buckets OR.Buckets.Read"
    })
    return requests.post(
        "https://staging.uipath.com/identity_/connect/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=payload
    ).json()["access_token"]


def fetch_file_from_bucket(file_name: str, token: str) -> bytes:
    """Fetch file bytes from Storage Bucket via signed URL."""
    orch_headers = {
        "Authorization":               f"Bearer {token}",
        "Content-Type":                "application/json",
        "X-UIPATH-OrganizationUnitId": FOLDER_ID
    }
    uri_resp = requests.get(
        f"{ORCH_URL}/odata/Buckets({BUCKET_ID})/UiPath.Server.Configuration.OData.GetReadUri",
        headers=orch_headers,
        params={"path": file_name}
    )
    if uri_resp.status_code != 200:
        raise Exception(f"Failed to get signed URL for {file_name}: {uri_resp.text}")

    signed_url = uri_resp.json()["Uri"]
    file_bytes  = requests.get(signed_url, stream=True).content
    logger.info(f"Fetched {file_name} from bucket ✅ Size: {len(file_bytes)} bytes")
    return file_bytes


def detect_acord_type(text: str) -> tuple[bool, str | None]:
    """
    Detect if document is an ACORD form and which type.
    Returns (is_acord, acord_type)
    """
    text_lower = text.lower()

    # First check if it's any ACORD at all
    if "acord" not in text_lower:
        return False, None

    # Then detect which type
    for acord_type, keywords in ACORD_TYPES.items():
        if any(kw in text_lower for kw in keywords):
            return True, acord_type

    # It's an ACORD but type not recognized
    return True, "ACORD Unknown"


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract raw text from PDF bytes using pypdf."""
    import io
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text   = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        logger.error(f"Text extraction failed: {str(e)}")
        return ""


def validate_attachment(file_name: str, token: str) -> ProcessingResult:
    """
    Fetch file from bucket, extract text, detect ACORD type.
    Returns a ProcessingResult dict.
    """
    try:
        # Fetch from bucket
        file_bytes = fetch_file_from_bucket(file_name, token)

        # Extract text
        text = extract_text_from_pdf(file_bytes)

        if not text.strip():
            return {
                "attachment_name": file_name,
                "is_acord":        False,
                "acord_type":      None,
                "is_blank":        True,
                "pages_in_order":  True,
                "is_valid":        False,
                "reason":          "No text extracted — may be scanned/blank",
                "cleaned_file_path": None
            }

        # Detect ACORD type
        is_acord, acord_type = detect_acord_type(text)

        return {
            "attachment_name":   file_name,
            "is_acord":          is_acord,
            "acord_type":        acord_type,
            "is_blank":          False,
            "pages_in_order":    True,
            "is_valid":          is_acord,
            "reason":            None if is_acord else "Not an ACORD document",
            "cleaned_file_path": None  # no cleaning needed at this stage
        }

    except Exception as e:
        logger.error(f"Validation failed for {file_name}: {str(e)}")
        return {
            "attachment_name":   file_name,
            "is_acord":          False,
            "acord_type":        None,
            "is_blank":          False,
            "pages_in_order":    False,
            "is_valid":          False,
            "reason":            str(e),
            "cleaned_file_path": None
        }


async def filter_and_classify_node(state: StateModel) -> Dict[str, Any]:
    """
    Filter and Classify node: Fetches attachments from Storage Bucket,
    validates if they are ACORD documents and detects the type.
    """
    logger.info("Executing Filter & Classify Node...")

    token   = get_token()
    results = []

    for attachment in state.attachments:
        file_name = attachment.full_name + ".pdf"
        logger.info(f"Validating attachment: {file_name}")
        result = validate_attachment(file_name, token)
        results.append(result)
        logger.info(f"  is_acord={result['is_acord']} | acord_type={result['acord_type']} | is_valid={result['is_valid']}")

    return {"filtering_results": results}