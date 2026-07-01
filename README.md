# 🏆 ADRO ACORD AI — UiPath Hackathon 2026
 
> **Intelligent Insurance Document Processing powered by UiPath Agent Framework + LangGraph**
 
![Architecture](docs/architecture.png)
 
---
 
## 1. 📌 Project Description
 
**ADRO ACORD AI** is a multi-agent automation solution that intelligently processes insurance-related broker emails and ACORD documents end-to-end.
 
**Problem it solves:** Insurance brokers send submission emails with attached ACORD forms (ACORD 125, ACORD 126, etc.) that today must be manually read, classified, and re-keyed into downstream systems such as Guidewire or a CRM. This manual triage is slow, error-prone, and doesn't scale during high submission volume — leading to delayed quotes, inconsistent data entry, and lost broker business.
 
**What the solution does:** ADRO ACORD AI automates this entire workflow. It ingests incoming broker emails, classifies the sender's intent, identifies which ACORD form type was submitted, extracts structured data fields from that form with confidence scoring, and routes the result either straight into downstream systems (high confidence) or to a human broker-review step (low confidence, via an automatically generated acknowledgement email). The result is a fully auditable, end-to-end pipeline that turns unstructured broker email + PDF attachments into clean, structured, system-ready data — with a human safety net built in.
 
Built for the **UiPath Hackathon 2026**, this solution demonstrates **UiPath Maestro**, **LangGraph**, and **UiPath Agent Builder** working together in a single cohesive multi-agent pipeline.
 
---
 
## 2. 🧩 UiPath Components Used
 
| Component | Purpose in this Solution |
|---|---|
| **UiPath Agent Builder** | Used to build the low-code sub-agents (ACORD Validator Agent) and to define agent entry points/bindings consumable by Orchestrator. |
| **UiPath Maestro (BPMN Engine)** | Orchestrates the business-process flow across the Classification & Orchestration layer, sequencing agent hand-offs according to a BPMN process definition. |
| **UiPath Orchestrator (Cloud/Staging)** | Hosts and triggers the Intent Classifier Agent, ACORD Classifier Agent, and Extraction Agent as Orchestrator processes; manages queues, jobs, and credentials. |
| **UiPath Data Fabric** | Supplies customer/context records (`CustomerRecords` entity) pulled at the start of the graph via `fetch_data_fabric`. |
| **UiPath `uipath` Python SDK / CLI** | Used to run, pack, publish, and evaluate the Master Agent (`uipath run`, `uipath pack`, `uipath publish`, `uipath eval`). |
| **UiPath Studio / Studio Web** | Used to import the `.uis` solution files, wire Orchestrator process references, and configure deployment. |
| **Storage Bucket** | Landing zone for ingested emails and ACORD attachments from the Email Ingestion Agent. |
| **HITL (Human-in-the-Loop) Review** | Broker-facing review step triggered for low-confidence classifications, closing the loop between automation and human judgment. |
| **Structured Data Repository → Guidewire / CRM Integration** | Final integration layer that pushes validated, extracted data into downstream enterprise systems. |
 
**Supporting (non-UiPath) technology:**
 
| Layer | Technology |
|---|---|
| Graph Runtime | LangGraph (`StateGraph`) |
| LLM Backend | Google Gemini API / Hugging Face TGI Endpoint |
| Language | Python 3.11+ |
 
---
 
## 3. 🤖 Agent Type
 
**This solution uses a hybrid of Coded Agents and Low-Code Agents:**
 
- **Coded Agent:** The **Master Agent** (this repository) is a fully coded agent — a Python/LangGraph `StateGraph` (`Agent/graph.py`) that defines the orchestration logic, node routing, and state schema (`Agent/state.py`) in code. It exposes a single async entry point (`agent_main`) consumable by UiPath Studio/Orchestrator.
- **Low-Code Agents:** The **Intent Classifier Agent**, **ACORD Classifier Agent**, and **ACORD Validator Agent** are built using **UiPath Agent Builder** (low-code) and invoked as Orchestrator jobs/processes from within the coded graph.
- **Process Orchestration:** **UiPath Maestro** provides a low-code BPMN layer coordinating the classification and orchestration stage above the coded Master Agent.
In short: the top-level control flow and state management are **code-first (Python/LangGraph)**, while the individual classification/validation capabilities are implemented as **low-code UiPath agents** invoked as tools/sub-processes — combining the flexibility of code with the speed of low-code agent building.
 
---
 
## 4. 🏗️ Solution Architecture
 
```
ACORD Document Processing System (Multi-Agent Architecture)
│
├── 1. Ingestion Layer          — Email Ingestion Agent → Storage Bucket
├── 2. Classification & Orchestration — Classification Agent + UiPath Maestro BPMN Engine
│                                       → Master Agent (Orchestrator)
├── 3. Extraction & Validation  — ACORD AI Service Center
│       ├── ACORD Classification (LLM — pre-trained model identification)
│       ├── ACORD Extraction    (LLM — high-confidence field extraction)
│       └── ACORD Validator Agent (UiPath Agent Builder)
├── 4. Human Collaboration      — HITL Broker Review (low-confidence fallback)
└── 5. Integration Layer        — Structured Data Repository → Guidewire / CRM
```
 
### Agent Graph Flow
 
```
START
  └─► fetch_data_fabric
        └─► intent_classification
              └─► master_router
                    ├─► [confidence < threshold] generate_ack ──► postprocess ──► END
                    └─► [confidence ≥ threshold] classify_acord
                              └─► extraction
                                    └─► postprocess ──► END
```
 
### Node Descriptions
 
| Node | Role |
|------|------|
| `fetch_data_fabric` | Pulls customer context from UiPath Data Fabric |
| `intent_classification` | Invokes the Intent Classifier Agent on Orchestrator to determine email intent |
| `master_router` | Routes to ACK generation (low confidence) or ACORD classification (high confidence) |
| `generate_ack` | Generates an acknowledgement email for broker when intent is unclear |
| `classify_acord` | Identifies the ACORD form type (125, 126, etc.) using LLM classification |
| `extraction` | Extracts structured data fields from the identified ACORD form |
| `postprocess` | Assembles final output, audit log, and flags for downstream integration |
 
### Project Structure
 
```
MasterAgentSolution/
├── Agent/
│   ├── main.py                     # UiPath entry point (agent_main)
│   ├── graph.py                    # LangGraph StateGraph definition
│   ├── state.py                    # Pydantic state schemas
│   ├── entry-points.json           # UiPath Agent entry-point manifest
│   ├── bindings.json               # Tool/skill bindings
│   ├── agent.mermaid               # Agent graph visualization
│   ├── AGENTS.md                   # Agent patterns reference
│   ├── .env.example                # Environment variable template
│   ├── nodes/
│   │   ├── intent_classifier.py    # Orchestrator job invocation for intent
│   │   ├── acord_classifier.py     # ACORD form type identification
│   │   ├── extractor.py            # Structured field extraction
│   │   ├── ack_generator.py        # Acknowledgement email generation
│   │   ├── data_fabric.py          # UiPath Data Fabric integration
│   │   ├── router.py               # Conditional routing logic
│   │   └── postprocess.py          # Output assembly & audit logging
│   └── evaluations/
│       ├── eval-sets/
│       └── evaluators/
├── ACORD_Framework.uis             # UiPath ACORD Framework solution
├── MasterAgentSolution (1).uis     # UiPath Master Agent solution
├── MasterAgentSolution.uipx        # Published agent package
└── SolutionStorage.json            # Solution metadata
```
 
---
 
## 5. 🚀 Setup Instructions (Step-by-Step)
 
### Prerequisites
 
Before you begin, make sure you have:
 
- [ ] Python 3.11 or higher installed
- [ ] A UiPath Orchestrator account (Staging or Cloud)
- [ ] UiPath Studio / Studio Web installed
- [ ] A Google API Key **or** a Hugging Face inference endpoint
- [ ] The `uipath` Python SDK installed (`pip install uipath`)
- [ ] Git installed
### Step 1 — Clone the Repository
 
```bash
git clone https://github.com/<your-org>/adro-acord-ai.git
cd adro-acord-ai/Agent
```
 
### Step 2 — Set Up Environment Variables
 
Copy the example environment file:
 
```bash
cp .env.example .env
```
 
Open `.env` and fill in all required values:
 
```env
GOOGLE_API_KEY=your_google_api_key
 
# Hugging Face (if using HF instead of Google)
HF_ENDPOINT_URL=https://your-hf-endpoint.com
HF_API_TOKEN=your_hf_token
HF_MODEL_NAME=tgi
 
# UiPath Orchestrator
MASTER_AGENT_API_KEY=your_api_key
JWT_SECRET_KEY=your_jwt_secret
 
# Confidence threshold for routing decisions
CONFIDENCE_THRESHOLD=0.80
 
# UiPath Orchestrator Process Names
INTENT_AGENT_NAME=IntentClassifierAgent
ACORD_AGENT_NAME=ACORDClassifierAgent
EXTRACTION_AGENT_NAME=FinalExtractionAgent
 
# UiPath Data Fabric
DATA_FABRIC_ENTITY=CustomerRecords
 
# Set to "true" for local testing without Orchestrator
MOCK_MODE=false
```
 
### Step 3 — Install Dependencies
 
```bash
pip install -r requirements.txt
```
 
### Step 4 — Run Locally in Mock Mode (No Orchestrator Required)
 
Set `MOCK_MODE=true` in `.env`, then run:
 
```bash
uipath run agent '{"email_payload": {"subject": "New ACORD Submission", "body": "Please find attached ACORD 125 form for ABC Corp.", "sender": "broker@example.com", "received_at": "2026-06-29T10:00:00Z", "attachment_names": ["acord125.pdf"], "message_id": "msg-001"}, "confidence_threshold": 0.80}'
```
 
This runs the full graph end-to-end using simulated node outputs — useful for local development and quick judging without live UiPath infrastructure.
 
### Step 5 — Deploy to UiPath Orchestrator
 
Package the agent:
 
```bash
uipath pack
```
 
Publish it to Orchestrator:
 
```bash
uipath publish
```
 
### Step 6 — Import the Solution in UiPath Studio
 
1. Open **UiPath Studio**.
2. Import `MasterAgentSolution.uipx` (published agent package).
3. Import `ACORD_Framework.uis` and `MasterAgentSolution (1).uis` as needed for the sub-agent solutions.
4. In Orchestrator, configure the process references for:
   - `IntentClassifierAgent`
   - `ACORDClassifierAgent`
   - `FinalExtractionAgent`
5. Confirm the **Data Fabric** entity `CustomerRecords` is accessible from your tenant.
### Step 7 — Run Evaluations
 
```bash
uipath eval --eval-set evaluations/eval-sets/evaluation-set-default.json
```
 
This validates the agent's classification and extraction accuracy against the provided evaluation set.
 
---
 
## 6. 📥 Agent Input / Output
 
### Input Schema
 
```json
{
  "email_payload": {
    "subject": "string",
    "body": "string",
    "sender": "string (email)",
    "received_at": "string (ISO 8601)",
    "attachment_names": ["string"],
    "message_id": "string"
  },
  "confidence_threshold": 0.80
}
```
 
### Output Schema
 
```json
{
  "intent": "string",
  "acord_type": "string (e.g. ACORD 125)",
  "extraction": { "...": "structured fields" },
  "ack_email": "string (generated email body, if low confidence)",
  "audit": [{ "step": "...", "timestamp": "..." }]
}
```
 
---
 
## 7. 🔀 Routing Logic
 
The `master_router` applies a configurable confidence threshold (default **0.80**) after intent classification:
 
- **Confidence ≥ threshold** → Proceeds to ACORD Classification → Field Extraction → Output
- **Confidence < threshold** → Generates an acknowledgement email for the broker → HITL Review
---
 
## 8. 🧪 Mock Mode
 
Set `MOCK_MODE=true` in `.env` to run the pipeline without calling live Orchestrator processes. Mock nodes return realistic simulated outputs and are useful for local development and CI testing.
 
---
 
## 👥 Team
 
Built by **Team ADRO** at the UiPath Hackathon 2026.
 
---
 
## 📄 License
 
This project was created for the UiPath Hackathon 2026. All rights reserved by the respective team members.
 
---
 
## 🙏 Acknowledgements
 
- [UiPath Agent Framework](https://docs.uipath.com/agent-builder)
- [UiPath Maestro](https://docs.uipath.com/maestro)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- ACORD Standards Organization for the ACORD form specifications
