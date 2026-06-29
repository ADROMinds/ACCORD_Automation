# 🏆 ADRO ACORD AI — UiPath Hackathon 2026

> **Intelligent Insurance Document Processing powered by UiPath Agent Framework + LangGraph**

![Architecture](docs/architecture.png)

---

## 📌 Overview

**ADRO ACORD AI** is a multi-agent automation solution built on the **UiPath ACORD Framework** that intelligently processes insurance-related broker emails and ACORD documents end-to-end. The system classifies incoming emails, identifies ACORD form types (e.g., ACORD 125, ACORD 126), extracts structured data fields, and routes documents to downstream enterprise systems — with Human-in-the-Loop (HITL) support for low-confidence cases.

Built for the **UiPath Hackathon 2026**, this solution demonstrates the power of **UiPath Maestro**, **LangGraph**, and **UiPath Agent Builder** working together in a cohesive multi-agent pipeline.

---

## 🏗️ Solution Architecture

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

The **Master Agent** (this repo) is the orchestration brain: it wires together all sub-agents via a LangGraph `StateGraph` and exposes a single async entry point consumable by UiPath Studio / Orchestrator.

---

## 🧠 Agent Graph Flow

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

---

## 📁 Project Structure

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

## ⚙️ Technology Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | UiPath Agent Builder + UiPath Maestro BPMN Engine |
| Orchestration | UiPath Orchestrator (Staging) |
| Graph Runtime | LangGraph (`StateGraph`) |
| LLM Backend | Google Gemini API / Hugging Face TGI Endpoint |
| Data Integration | UiPath Data Fabric |
| Language | Python 3.14 |
| Deployment | UiPath Studio Web / Cloud Orchestrator |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- UiPath Orchestrator account (Staging or Cloud)
- UiPath Studio / Studio Web
- Google API Key or Hugging Face endpoint
- `uipath` Python SDK installed

### 1. Clone the Repository

```bash
git clone https://github.com/<your-org>/adro-acord-ai.git
cd adro-acord-ai/Agent
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in all required values:

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

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Locally (Mock Mode)

To test the agent locally without a live Orchestrator connection:

```bash
# Set MOCK_MODE=true in your .env, then:
uipath run agent '{"email_payload": {"subject": "New ACORD Submission", "body": "Please find attached ACORD 125 form for ABC Corp.", "sender": "broker@example.com", "received_at": "2026-06-29T10:00:00Z", "attachment_names": ["acord125.pdf"], "message_id": "msg-001"}, "confidence_threshold": 0.80}'
```

### 5. Deploy to UiPath Orchestrator

```bash
# Package the agent
uipath pack

# Publish to Orchestrator
uipath publish
```

Then import `MasterAgentSolution.uipx` in UiPath Studio and configure the Orchestrator process references.

### 6. Run Evaluations

```bash
uipath eval --eval-set evaluations/eval-sets/evaluation-set-default.json
```

---

## 📥 Agent Input / Output

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

## 🔀 Routing Logic

The `master_router` applies a configurable confidence threshold (default **0.80**) after intent classification:

- **Confidence ≥ threshold** → Proceeds to ACORD Classification → Field Extraction → Output
- **Confidence < threshold** → Generates an acknowledgement email for the broker → HITL Review

---

## 🧪 Mock Mode

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
