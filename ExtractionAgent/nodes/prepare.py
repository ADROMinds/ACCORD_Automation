import os
import logging
import requests
from typing import Dict, Any
from urllib.parse import urlencode
from langchain_core.messages import HumanMessage, SystemMessage
from state import InputModel

logger = logging.getLogger(__name__)

# ── Credentials & Config ─────────────────────────────────────────────────────
CLIENT_ID     = "29e4161e-9863-44a6-b5dc-a0e7da356ac7"
CLIENT_SECRET = "XMloS2Mr_HoaXSxAf8_7U9W*OUqA5BZAYNNDb9A2#d%VK@^LI7f0RQ#xU7Ky9meu"
ORG           = "hackathon26_585"
TENANT        = "DefaultTenant"
FOLDER_ID     = "3084015"
BUCKET_ID     = "218383"
PROJECT_ID    = "1707af7d-14d1-80bc-9783-73a0ce3e9fb5"
EXTRACTOR_ID  = "gpt_ixp_10"
ORCH_URL      = f"https://staging.uipath.com/{ORG}/{TENANT}/orchestrator_"
DU_URL        = f"https://staging.uipath.com/{ORG}/{TENANT}/du_"

SYSTEM_PROMPT = (
    "You are a document processing assistant. "
    "Analyze the document filtering results and extraction data to provide a final summary."
)


def get_token() -> str:
    payload = urlencode({
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope":         "OR.Jobs OR.Execution OR.Folders OR.Buckets OR.Buckets.Read Du.Extraction.Api Du.Digitization.Api"
    })
    return requests.post(
        "https://staging.uipath.com/identity_/connect/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=payload
    ).json()["access_token"]


def run_health_check(token: str, file_names: list[str]) -> None:
    """Runs health check on Storage Bucket files and IXP models."""

    orch_headers = {
        "Authorization":               f"Bearer {token}",
        "Content-Type":                "application/json",
        "X-UIPATH-OrganizationUnitId": FOLDER_ID
    }
    du_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }

    logger.info("=" * 60)
    logger.info("HEALTH CHECK")
    logger.info("=" * 60)

    # ── Check 1: Each file exists in Storage Bucket ───────────────────────────
    for file_name in file_names:
        logger.info(f"[1] Checking file in Storage Bucket: {file_name}")
        uri_resp = requests.get(
            f"{ORCH_URL}/odata/Buckets({BUCKET_ID})/UiPath.Server.Configuration.OData.GetReadUri",
            headers=orch_headers,
            params={"path": file_name}
        )
        if uri_resp.status_code == 200:
            logger.info(f"    ✅ File found: {file_name}")
        else:
            raise Exception(f"❌ File NOT found in bucket: {file_name} | {uri_resp.text}")

    # ── Check 2: IXP Project is accessible ───────────────────────────────────
    logger.info(f"[2] Checking IXP Project: {PROJECT_ID}")
    project_resp = requests.get(
        f"{DU_URL}/api/framework/projects/{PROJECT_ID}?api-version=1",
        headers=du_headers
    )
    if project_resp.status_code == 200:
        project = project_resp.json()
        logger.info(f"    ✅ Project found: {project.get('name')} | Type: {project.get('type')}")
    else:
        raise Exception(f"❌ IXP Project NOT accessible: {project_resp.text}")

    # ── Check 3: IXP Extractor is available ──────────────────────────────────
    logger.info(f"[3] Checking IXP Extractor: {EXTRACTOR_ID}")
    extractors_resp = requests.get(
        f"{DU_URL}/api/framework/projects/{PROJECT_ID}/extractors?api-version=1",
        headers=du_headers
    )
    if extractors_resp.status_code == 200:
        extractors = extractors_resp.json().get("extractors", [])
        match = next((e for e in extractors if e.get("id") == EXTRACTOR_ID), None)
        if match:
            logger.info(f"    ✅ Extractor found: {match.get('name')} | Status: {match.get('status')} | Version: {match.get('projectVersionName')}")
        else:
            raise Exception(f"❌ Extractor {EXTRACTOR_ID} not found in project")
    else:
        raise Exception(f"❌ Could not fetch extractors: {extractors_resp.text}")

    logger.info("=" * 60)
    logger.info("HEALTH CHECK PASSED ✅")
    logger.info("=" * 60)


async def prepare_node(input_data: InputModel) -> Dict[str, Any]:
    """
    Preparation node: Runs health check, initializes message state
    and sets up attachments for processing.
    """
    logger.info("Executing Prepare Node...")

    # ── Run Health Check ──────────────────────────────────────────────────────
    try:
        token      = get_token()
        file_names = [a.full_name + ".pdf" for a in input_data.attachments]
        run_health_check(token, file_names)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise e

    return {
        "attachments": input_data.attachments,
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content="Process the following attachments."),
        ],
    }