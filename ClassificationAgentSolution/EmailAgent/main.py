from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from uipath_langchain.chat.models import UiPathAzureChatOpenAI
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
import os

class EmailPayload(BaseModel):
    subject: str = Field(description="Subject of the email")
    body: str = Field(description="Body content of the email")
    sender: str = Field(description="Sender's email address")
    received_at: str = Field(description="Timestamp when the email was received")
    attachment_names: list[str] = Field(description="List of attachment filenames")
    message_id: str = Field(description="Unique identifier for the message")

class EmailInput(BaseModel):
    email_payload: EmailPayload = Field(description="The email payload to analyze")
    confidence_threshold: float = Field(default=0.8, description="The confidence threshold for detection")

class EmailOutput(BaseModel):
    intent: str = Field(description="The detected intent of the email")
    summary: str = Field(description="A brief summary of the email content")
    confidence: float = Field(description="The confidence score (0.0 to 1.0) for the detected intent")

class GraphState(BaseModel):
    email_payload: EmailPayload
    confidence_threshold: float
    intent: str | None = None
    summary: str | None = None
    confidence: float | None = None

async def analyze_email(state: GraphState) -> dict:
    # Model name might need to be verified in the tenant
    llm = UiPathAzureChatOpenAI(
    model="gpt-4o-mini-2024-07-18"
    )
    
    structured_llm = llm.with_structured_output(EmailOutput)
    
    system_prompt = (
        "You are an expert email analyst. Analyze the provided email payload to "
        "determine its primary intent, provide a concise summary, and assign a "
        "confidence score (0.0 to 1.0) for your intent classification. "
        f"Ensure your analysis respects a confidence threshold of {state.confidence_threshold}."
    )
    
    human_content = (
        f"Subject: {state.email_payload.subject}\n"
        f"Sender: {state.email_payload.sender}\n"
        f"Body: {state.email_payload.body}\n"
        f"Attachments: {', '.join(state.email_payload.attachment_names)}"
    )
    
    result = await structured_llm.ainvoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=human_content)]
    )
    
    # result is an EmailOutput object
    return {
        "intent":     result.intent,
        "summary":    result.summary,
        "confidence": result.confidence
    }

builder = StateGraph(GraphState, input_schema=EmailInput, output_schema=EmailOutput)

builder.add_node("analyze_email", analyze_email)

builder.add_edge(START, "analyze_email")
builder.add_edge("analyze_email", END)

graph = builder.compile()
