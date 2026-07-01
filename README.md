# 🏆 ADRO ACORD AI — UiPath Hackathon 2026
 
> **Intelligent Insurance Document Processing powered by UiPath Agent Framework + LangGraph**
 

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
└── 4. Integration Layer        — Structured Data Repository → Guidewire / CRM
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
git clone https://github.com/ADROMinds/ACCORD_Automation.git
cd ACCORD_Automation
```

---

### Step 2 — Configure Environment Variables

Create a `.env` file in the project root and configure the required environment variables.

```env
GOOGLE_API_KEY=your_google_api_key

# Hugging Face (Optional)
HF_ENDPOINT_URL=https://your-hf-endpoint.com
HF_API_TOKEN=your_hf_token
HF_MODEL_NAME=tgi

# UiPath Orchestrator
MASTER_AGENT_API_KEY=your_api_key
JWT_SECRET_KEY=your_jwt_secret

# Confidence Threshold
CONFIDENCE_THRESHOLD=0.80

# UiPath Process Names
INTENT_AGENT_NAME=IntentClassifierAgent
ACORD_AGENT_NAME=ACORDClassifierAgent
EXTRACTION_AGENT_NAME=FinalExtractionAgent

# Data Fabric
DATA_FABRIC_ENTITY=CustomerRecords

# Local Testing
MOCK_MODE=false
```

---

### Step 3 — Open the Projects

Open the required projects in **UiPath Studio**.

```
ACCORD Framework/
ClassificationAgentSolution/
ExtractionAgent/
MasterAgentSolution/
```

Restore the project dependencies if prompted.

---

### Step 4 — Publish to UiPath Orchestrator

Publish the following projects from UiPath Studio to your UiPath Orchestrator tenant.

- ACORD Framework
- ClassificationAgentSolution
- ExtractionAgent
- MasterAgentSolution

After publishing, create the corresponding **Processes** in Orchestrator.

---

### Step 5 — Configure Orchestrator

Ensure the following processes are available and correctly configured.

- IntentClassifierAgent
- ACORDClassifierAgent
- FinalExtractionAgent

Also verify that the required **Data Fabric** entity (`CustomerRecords`) is accessible.

---

### Step 6 — Execute the Master Agent

Run the **MasterAgentSolution** from UiPath Studio or Orchestrator.

The workflow automatically performs:

1. Email Intent Classification
2. ACORD Document Classification
3. Data Extraction
4. Validation
5. Human-in-the-Loop routing (if confidence is below threshold)
6. Final structured output generation

---

## 📥 Agent Input

```json
{
  "email_payload": {
    "subject": "string",
    "body": "string",
    "sender": "string",
    "received_at": "ISO 8601",
    "attachment_names": [
      "string"
    ],
    "message_id": "string"
  },
  "confidence_threshold": 0.80
}
```

---

## 📤 Agent Output

```json
{
  "intent": "string",
  "acord_type": "string",
  "extraction": {
    "...": "structured fields"
  },
  "ack_email": "string",
  "audit": [
    {
      "step": "...",
      "timestamp": "..."
    }
  ]
}
```

---

## 🔀 Routing Logic

The Master Agent uses a configurable confidence threshold (default **0.80**) after intent classification.

- **Confidence ≥ 0.80** → ACORD Classification → Data Extraction → Validation → Output
- **Confidence < 0.80** → Generate acknowledgement email → Human-in-the-Loop review

---

## 🧪 Mock Mode

Set

```env
MOCK_MODE=true
```

to execute the workflow using simulated outputs instead of live UiPath Orchestrator processes. This is useful for local development, testing, and demonstrations.
 
## 👥 Team
 
Built by **Team ADROMinds** at the  **[UiPath Hackathon – AgentHack 2026](https://uipath-agenthack.devpost.com/)**.
 
---
 
## 📄 License
 
This project was created for the **[UiPath Hackathon – AgentHack 2026](https://uipath-agenthack.devpost.com/)**. All rights reserved by the respective team members.
 
---
 
## 🙏 Acknowledgements
 
- [UiPath Agent Framework](https://docs.uipath.com/agent-builder)
- [UiPath Maestro](https://docs.uipath.com/maestro)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- ACORD Standards Organization for the ACORD form specifications
