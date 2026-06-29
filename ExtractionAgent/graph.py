import logging
from langgraph.graph import START, END, StateGraph
from state import StateModel, InputModel, AgentResponse

from nodes.prepare import prepare_node
from nodes.filter_and_classify import filter_and_classify_node
from nodes.ixp_extraction import ixp_extraction_node
from nodes.postprocess import postprocess_node

# Configure logger
logger = logging.getLogger(__name__)

# Initialize StateGraph with modular nodes and schemas
builder = StateGraph(StateModel, input=InputModel, output=AgentResponse)

builder.add_node("prepare", prepare_node)
builder.add_node("filter_and_classify", filter_and_classify_node)
builder.add_node("ixp_extraction", ixp_extraction_node)
builder.add_node("postprocess", postprocess_node)

# Define Edges
builder.add_edge(START, "prepare")
builder.add_edge("prepare", "filter_and_classify")
builder.add_edge("filter_and_classify", "ixp_extraction")
builder.add_edge("ixp_extraction", "postprocess")
builder.add_edge("postprocess", END)

# Compile Application
graph = builder.compile()
