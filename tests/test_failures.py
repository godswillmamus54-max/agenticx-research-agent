from langchain_core.messages import AIMessage

from app.graph import (
    execute_tools_node,
    finalize_node,
    route_after_agent,
    route_after_tools,
)
from app.state import ResearchState


def test_hard_step_limit_routes_to_finish():
    state: ResearchState = {
        "question": "Test question",
        "step_count": 6,
        "max_steps": 6,
        "messages": [],
        "tool_calls": [],
        "tool_results": [],
        "sources": [],
        "discovered_sources": [],
        "fetched_sources": [],
        "errors": [],
        "pending_fetches": 0,
        "status": "limit_reached",
    }

    assert route_after_agent(state) == "finish"


def test_tool_failure_is_recorded():
    state: ResearchState = {
        "question": "Test question",
        "messages": [],
        "tool_calls": [],
        "tool_results": [],
        "sources": [],
        "discovered_sources": [],
        "fetched_sources": [],
        "errors": [],
        "pending_fetches": 0,
        "status": "starting",
    }

    result = execute_tools_node(state)

    assert result["status"] == "failed"
    assert result["errors"]


def test_limit_finalize_is_graceful():
    state: ResearchState = {
        "question": "Test question",
        "messages": [],
        "step_count": 6,
        "max_steps": 6,
        "messages": [],
        "sources": [],
        "discovered_sources": [],
        "fetched_sources": [
            {
                "title": "Example Source",
                "url": "https://example.com",
                "source_type": "fetched",
            }
        ],
        "errors": [],
        "pending_fetches": 0,
        "status": "limit_reached",
    }

    result = finalize_node(state)

    assert result["status"] == "limit_reached"
    assert "hard step limit" in result["final_answer"]
    assert "1 source" in result["final_answer"]


def test_agent_without_evidence_is_forced_to_research():
    state: ResearchState = {
        "question": "Test question",
        "step_count": 1,
        "max_steps": 6,
        "messages": [
            AIMessage(
                content="I should answer now."
            )
        ],
        "fetched_sources": [],
        "status": "completed",
    }

    result = route_after_agent(state)

    assert result == "research"


def test_tool_phase_returns_to_research():
    state: ResearchState = {
        "question": "Test question",
        "step_count": 1,
        "max_steps": 6,
        "pending_fetches": 5,
        "fetched_sources": [],
        "status": "tool_executed",
    }

    assert route_after_tools(state) == "research"


def test_fetched_evidence_allows_progress():
    state: ResearchState = {
        "question": "Test question",
        "step_count": 2,
        "max_steps": 6,
        "pending_fetches": 4,
        "fetched_sources": [
            {
                "title": "Example",
                "url": "https://example.com",
                "source_type": "fetched",
            }
        ],
        "status": "tool_executed",
    }

    assert route_after_tools(state) == "research"