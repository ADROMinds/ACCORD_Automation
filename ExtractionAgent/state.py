from typing import Annotated, Any, TypedDict, Optional
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages
from uipath.platform.attachments import Attachment

class InputModel(BaseModel):
    attachments: list[Attachment] = Field(
        default_factory=list,
        description="List of document attachments to process (e.g., ACORD forms)."
    )
    mock_mode: bool = Field(
        default=True,
        description="If true, returns mock extraction data instead of calling live models."
    )

class ProcessingResult(TypedDict):
    attachment_name: str
    is_acord: bool
    acord_type: Optional[str]
    is_blank: bool
    pages_in_order: bool
    is_valid: bool
    reason: Optional[str]
    cleaned_file_path: Optional[str]

class AgentResponse(TypedDict):
    filtering_results: list[ProcessingResult]
    extraction_results: list[dict[str, Any]]
    summary: str

class StateModel(BaseModel):
    messages: Annotated[list[Any], add_messages] = []
    attachments: list[Attachment] = []
    mock_mode: bool = True
    filtering_results: list[ProcessingResult] = []
    extraction_results: list[dict[str, Any]] = []
