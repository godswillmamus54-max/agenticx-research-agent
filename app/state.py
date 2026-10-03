from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


def append_list(existing: List[Any], new: List[Any]) -> List[Any]:
    """Append new list items to the existing state list."""
    return existing + new


class ResearchState(TypedDict, total=False):
    question: str

    messages: Annotated[
        List[AnyMessage],
        add_messages,
    ]

    # One step = one research-agent decision cycle.
    step_count: int
    max_steps: int

    next_action: Optional[str]
    action_input: Optional[str]

    tool_calls: Annotated[
        List[Dict[str, Any]],
        append_list,
    ]

    tool_results: Annotated[
        List[Dict[str, Any]],
        append_list,
    ]

    # Sources discovered by search_web.
    discovered_sources: Annotated[
        List[Dict[str, Any]],
        append_list,
    ]

    # Pages successfully retrieved by fetch_page.
    fetched_sources: Annotated[
        List[Dict[str, Any]],
        append_list,
    ]

    # Combined source history.
    sources: Annotated[
        List[Dict[str, Any]],
        append_list,
    ]

    errors: Annotated[
        List[str],
        append_list,
    ]

    # Number of discovered sources still needing retrieval.
    pending_fetches: int

    final_answer: Optional[str]

    status: str