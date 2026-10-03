from app.state import ResearchState


def test_research_state_can_store_core_fields():
    state: ResearchState = {
        "question": "What causes inflation?",
        "step_count": 0,
        "max_steps": 6,
        "tool_calls": [],
        "tool_results": [],
        "sources": [],
        "errors": [],
        "status": "starting",
    }

    assert state["question"] == "What causes inflation?"
    assert state["step_count"] == 0
    assert state["max_steps"] == 6
    assert state["status"] == "starting"