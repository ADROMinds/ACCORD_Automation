import os
import logging
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from uipath_langchain.chat import UiPathAzureChatOpenAI
from state import StateModel, AgentResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a document processing assistant. "
    "Analyze the document filtering results and extraction data to provide a final summary."
)

async def postprocess_node(state: StateModel) -> AgentResponse:
    """
    Postprocess node: Summarizes filtering and extraction results using an LLM or mock formatter.
    """
    logger.info("Executing Postprocess Node...")
    
    env_mock = os.environ.get("UIPATH_MOCK_MODE", "").lower()
    is_mock = env_mock == "true" or (env_mock != "false" and state.mock_mode)

    if is_mock:
        logger.info("[MOCK] Simulating Postprocess Summary...")
        summary_text = (
            f"Processed {len(state.filtering_results)} attachment(s). "
            f"Successfully extracted data for {len(state.extraction_results)} document(s) in Mock Mode."
        )
        return AgentResponse(
            filtering_results=state.filtering_results,
            extraction_results=state.extraction_results,
            summary=summary_text
        )

    logger.info("Running live LLM summary postprocessing...")
    
    # ==========================================
    # USER IMPLEMENTATION SPACE - LLM SUMMARY
    # ==========================================
    try:
        llm = UiPathAzureChatOpenAI(model=os.getenv("AZURE_OPENAI_MODEL", "gpt-4.1-mini-2025-04-14"))
        summary_input = f"Filtering results: {state.filtering_results}\nExtraction results: {state.extraction_results}"
        
        response = await llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Summarize these processing results: {summary_input}")
        ])
        summary_text = response.content
    except Exception as e:
        logger.error(f"Error generating LLM summary: {str(e)}")
        summary_text = f"Processed attachments with {len(state.extraction_results)} extraction results. (LLM summary unavailable: {str(e)})"
    # ==========================================
    # END OF USER IMPLEMENTATION SPACE
    # ==========================================
    
    return AgentResponse(
        filtering_results=state.filtering_results,
        extraction_results=state.extraction_results,
        summary=summary_text
    )
