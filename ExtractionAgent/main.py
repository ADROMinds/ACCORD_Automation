import logging
import asyncio
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from graph import graph
from state import InputModel, AgentResponse, StateModel, ProcessingResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def agent_main(attachments: List[Any] = None, mock_mode: bool = True) -> Dict[str, Any]:
    """
    Standard entry point for UiPath Studio Web Extraction Agent.
    Input arguments match InputModel schema.
    """
    logger.info("Extraction Agent invoked.")
    try:
        input_payload = InputModel(attachments=attachments or [], mock_mode=mock_mode)
        result = await graph.ainvoke(input_payload)
        return result
    except Exception as e:
        logger.error(f"Extraction Agent Execution Error: {str(e)}")
        return {"error": str(e), "status": "failed"}

def run_agent(attachments: List[Any] = None, mock_mode: bool = True) -> Dict[str, Any]:
    """
    Synchronous wrapper for local testing.
    """
    return asyncio.run(agent_main(attachments=attachments, mock_mode=mock_mode))

# Export 'graph' for LangGraph CLI / Studio Web runtime
__all__ = ["graph", "agent_main", "run_agent", "InputModel", "AgentResponse", "StateModel", "ProcessingResult"]
