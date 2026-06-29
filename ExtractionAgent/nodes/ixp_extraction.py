import os
import logging
import requests
import json
import time
from typing import Dict, Any
from urllib.parse import urlencode
from state import StateModel

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


def extract_document(file_name: str) -> Dict[str, Any]:
    """Full extraction pipeline for a single file from Storage Bucket."""

    token = get_token()
    logger.info("Token OK ✅")

    orch_headers = {
        "Authorization":               f"Bearer {token}",
        "Content-Type":                "application/json",
        "X-UIPATH-OrganizationUnitId": FOLDER_ID
    }
    du_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }

    # ── Step 1: Get Signed URL from Bucket ───────────────────────────────────
    logger.info(f"Fetching signed URL for: {file_name}")
    uri_resp = requests.get(
        f"{ORCH_URL}/odata/Buckets({BUCKET_ID})/UiPath.Server.Configuration.OData.GetReadUri",
        headers=orch_headers,
        params={"path": file_name}
    )
    if uri_resp.status_code != 200:
        raise Exception(f"Failed to get signed URL: {uri_resp.text}")
    signed_url = uri_resp.json()["Uri"]
    logger.info("Signed URL OK ✅")

    # ── Step 2: Stream file into memory ──────────────────────────────────────
    logger.info("Streaming file into memory...")
    file_bytes = requests.get(signed_url, stream=True).content
    logger.info(f"File in memory ✅ Size: {len(file_bytes)} bytes")

    # ── Step 3: Digitize ─────────────────────────────────────────────────────
    logger.info("Starting digitization...")
    digitize_resp = requests.post(
        f"{DU_URL}/api/framework/projects/{PROJECT_ID}/digitization/start?api-version=1",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (file_name, file_bytes, "application/pdf")}
    )
    if digitize_resp.status_code not in [200, 201, 202]:
        raise Exception(f"Digitization failed: {digitize_resp.text}")
    document_id = digitize_resp.json().get("documentId")
    logger.info(f"Document ID: {document_id} ✅")

    # ── Step 4: Poll Digitization ─────────────────────────────────────────────
    logger.info("Polling digitization status...")
    for i in range(30):
        status_resp = requests.get(
            f"{DU_URL}/api/framework/projects/{PROJECT_ID}/digitization/result/{document_id}?api-version=1",
            headers=du_headers
        )
        status = status_resp.json().get("status")
        logger.info(f"  [{i*3}s] Digitization Status: {status}")
        if status == "Succeeded":
            logger.info("Digitization Complete ✅")
            break
        elif status in ["Failed", "Error"]:
            raise Exception(f"Digitization failed: {status_resp.text}")
        time.sleep(3)

    # ── Step 5: Start Extraction ──────────────────────────────────────────────
    logger.info("Starting extraction...")
    extract_resp = requests.post(
        f"{DU_URL}/api/framework/projects/{PROJECT_ID}/extractors/{EXTRACTOR_ID}/extraction/start?api-version=1",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"documentId": document_id, "documentTypeId": "00000000-0000-0000-0000-000000000000"}
    )
    if extract_resp.status_code not in [200, 201, 202]:
        raise Exception(f"Extraction start failed: {extract_resp.text}")

    extract_body = extract_resp.json()
    operation_id = extract_body.get("operationId")
    result_url   = extract_body.get("resultUrl")
    logger.info(f"Operation ID: {operation_id} ✅")

    # ── Step 6: Poll Extraction ───────────────────────────────────────────────
    logger.info("Polling extraction status...")
    body = {}
    for i in range(60):
        result_resp = requests.get(
            result_url,
            headers={"Authorization": f"Bearer {token}"}
        )
        body   = result_resp.json()
        status = body.get("status")
        logger.info(f"  [{i*5}s] Extraction Status: {status}")
        if status == "Succeeded":
            logger.info("Extraction Complete ✅")
            break
        elif status in ["Failed", "Error"]:
            raise Exception(f"Extraction failed: {result_resp.text}")
        time.sleep(5)

    # ── Step 7: Upload Result to Bucket ──────────────────────────────────────
    logger.info("Uploading extraction result to Storage Bucket...")
    output_data = {
        "documentId":  document_id,
        "operationId": operation_id,
        "result":      body
    }
    json_bytes  = json.dumps(output_data, indent=2).encode("utf-8")
    result_file = f"extraction_result_{operation_id}.json"

    write_uri_resp = requests.get(
        f"{ORCH_URL}/odata/Buckets({BUCKET_ID})/UiPath.Server.Configuration.OData.GetWriteUri",
        headers=orch_headers,
        params={"path": result_file, "contentType": "application/json"}
    )
    if write_uri_resp.status_code != 200:
        raise Exception(f"Failed to get Write URI: {write_uri_resp.text}")

    upload_resp = requests.put(
        write_uri_resp.json()["Uri"],
        headers={"Content-Type": "application/json", "x-ms-blob-type": "BlockBlob"},
        data=json_bytes
    )
    if upload_resp.status_code in [200, 201]:
        logger.info(f"✅ Result uploaded: {result_file}")
    else:
        raise Exception(f"Upload failed: {upload_resp.text}")

    return {
        "documentId":  document_id,
        "operationId": operation_id,
        "result_file": result_file,
        "data":        body
    }


async def ixp_extraction_node(state: StateModel) -> Dict[str, Any]:
    """
    IXP Extraction node: Performs document extraction for all attachments.
    File name comes from state.attachments[i].FullName as input argument.
    """
    logger.info("Executing IXP Extraction Node...")

    extractions = []

    for attachment in state.attachments:
        file_name = attachment.full_name + ".pdf"
        logger.info(f"Processing file: {file_name}")

        try:
            result = extract_document(file_name)
            extractions.append({
                "attachment_id":   attachment.id,
                "attachment_name": file_name,
                "data":            result["data"],
                "result_file":     result["result_file"],
                "mode":            "LIVE"
            })
        except Exception as e:
            logger.error(f"Extraction failed for {file_name}: {str(e)}")
            extractions.append({
                "attachment_id":   attachment.id,
                "attachment_name": file_name,
                "data":            None,
                "error":           str(e),
                "mode":            "LIVE"
            })

    return {"extraction_results": extractions}