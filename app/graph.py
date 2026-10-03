from typing import Any, Dict, List

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from app.nodes import create_tool_enabled_model
from app.state import ResearchState
from app.tools import fetch_page, search_web


def _last_ai_message(state: ResearchState) -> AIMessage | None:
    """Return the most recent AI message, if one exists."""
    for message in reversed(state.get("messages", [])):
        if isinstance(message, AIMessage):
            return message

    return None


def _extract_tool_calls(message: AIMessage) -> List[Dict[str, Any]]:
    """Extract normalized tool-call information from an AI message."""
    calls: List[Dict[str, Any]] = []

    for call in message.tool_calls or []:
        calls.append(
            {
                "id": call.get("id"),
                "name": call.get("name"),
                "args": call.get("args", {}),
            }
        )

    return calls


def research_agent_node(state: ResearchState) -> Dict[str, Any]:
    """
    Run one LLM research decision cycle.

    The LLM can decide whether to search, fetch a page, or stop.
    The graph controls how that decision is routed.
    """
    model = create_tool_enabled_model()

    response = model.invoke(
        state.get("messages", [])
    )

    tool_calls = _extract_tool_calls(response)

    return {
        "messages": [response],
        "tool_calls": tool_calls,
        "step_count": state.get("step_count", 0) + 1,
    }


def execute_tools_node(state: ResearchState) -> Dict[str, Any]:
    """
    Execute tool calls requested by the research agent.

    Search results become discovered sources.
    Successfully fetched pages become verified evidence.
    """
    message = _last_ai_message(state)

    if message is None:
        return {
            "errors": [
                "No AI message available for tool execution."
            ],
            "status": "failed",
        }

    tool_messages = []
    tool_results = []
    discovered_sources = []
    fetched_sources = []
    errors = []

    pending_fetches = state.get(
        "pending_fetches",
        0,
    )

    for call in message.tool_calls or []:
        name = call.get("name")
        args = call.get("args", {})
        call_id = call.get("id")

        # ---------------------------------------------------------
        # SEARCH
        # ---------------------------------------------------------
        if name == "search_web":
            result = search_web.invoke(args)

            tool_results.append(
                {
                    "tool": name,
                    "ok": result.get("ok", False),
                    "result": result,
                }
            )

            if result.get("ok"):
                results = result.get(
                    "results",
                    [],
                )

                discovered_sources.extend(results)

                pending_fetches += len(results)

            else:
                errors.append(
                    result.get(
                        "error",
                        "Unknown search error.",
                    )
                )

            tool_messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=call_id,
                )
            )

        # ---------------------------------------------------------
        # FETCH
        # ---------------------------------------------------------
        elif name == "fetch_page":
            result = fetch_page.invoke(args)

            tool_results.append(
                {
                    "tool": name,
                    "ok": result.get("ok", False),
                    "result": result,
                }
            )

            if result.get("ok"):
                fetched_sources.append(
                    {
                        "url": result.get(
                            "url",
                            "",
                        ),
                        "title": result.get(
                            "title",
                            "",
                        ),
                        "text": result.get(
                            "text",
                            "",
                        ),
                    }
                )

                pending_fetches = max(
                    0,
                    pending_fetches - 1,
                )

            else:
                errors.append(
                    result.get(
                        "error",
                        "Unknown fetch error.",
                    )
                )

            tool_messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=call_id,
                )
            )

        # ---------------------------------------------------------
        # UNKNOWN TOOL
        # ---------------------------------------------------------
        else:
            error = (
                f"Unknown tool requested: {name}"
            )

            errors.append(error)

            tool_messages.append(
                ToolMessage(
                    content=error,
                    tool_call_id=call_id,
                )
            )

    return {
        "messages": tool_messages,
        "tool_results": tool_results,
        "discovered_sources": discovered_sources,
        "fetched_sources": fetched_sources,
        "sources": (
            discovered_sources
            + fetched_sources
        ),
        "errors": errors,
        "pending_fetches": pending_fetches,
    }


def build_evidence_packet(
    state: ResearchState,
) -> str:
    """
    Build a numbered evidence packet using ONLY successfully
    fetched sources.

    Search-result snippets are deliberately excluded.
    """
    fetched_sources = state.get(
        "fetched_sources",
        []
    )

    if not fetched_sources:
        return "NO FETCHED EVIDENCE IS AVAILABLE."

    sections = []

    for index, source in enumerate(
        fetched_sources,
        start=1,
    ):
        title = (
            source.get("title")
            or "Untitled source"
        )

        url = source.get(
            "url",
            "",
        )

        text = source.get(
            "text",
            "",
        )

        # Keep the evidence packet bounded.
        text = text[:10000]

        sections.append(
            f"[{index}] {title}\n"
            f"URL: {url}\n"
            f"EVIDENCE:\n{text}"
        )

    return "\n\n".join(sections)


def finalize_node(
    state: ResearchState,
) -> Dict[str, Any]:
    """
    Generate the final answer using only successfully fetched
    evidence.

    If the hard step limit was reached, explicitly tell the user
    that the answer is based only on the sources fetched before
    the limit.
    """
    previous_status = state.get(
        "status"
    )

    limit_reached = (
        previous_status == "limit_reached"
    )

    fetched_sources = state.get(
        "fetched_sources",
        []
    )

    source_count = len(
        fetched_sources
    )

    # ---------------------------------------------------------
    # NO VERIFIED EVIDENCE
    # ---------------------------------------------------------
    if not fetched_sources:

        if limit_reached:
            final_answer = (
                "The research agent reached its hard step limit "
                "before successfully fetching a source, so it "
                "could not produce a verified research answer."
            )
        else:
            final_answer = (
                "I could not produce a verified research answer "
                "because no source was successfully fetched."
            )

        return {
            "final_answer": final_answer,
            "status": (
                "limit_reached"
                if limit_reached
                else "completed"
            ),
        }

    # ---------------------------------------------------------
    # BUILD EVIDENCE
    # ---------------------------------------------------------
    question = state.get(
        "question",
        "",
    )

    evidence = build_evidence_packet(
        state
    )

    # ---------------------------------------------------------
    # FINAL ANSWER PROMPT
    # ---------------------------------------------------------
    final_prompt = f"""
You are the final evidence-grounded answer writer.

USER'S RESEARCH QUESTION:
{question}

The following are the ONLY sources you may use as factual
evidence:

{evidence}

STRICT EVIDENCE RULES:

1. Every factual claim must be supported by one or more
   successfully fetched sources above.

2. Cite factual claims immediately using [1], [2], [3], etc.

3. Each citation number corresponds to the fetched source
   with that number.

4. Never cite a source that was only discovered by search.

5. Never invent citation numbers.

6. Do not use general model knowledge to add unsupported facts.

7. If the fetched evidence does not establish a requested
   point, explicitly say that the available sources did not
   establish it.

8. Do not make a claim merely because it sounds generally true.

9. Prefer precise claims supported by the evidence.

10. Keep the answer concise and directly address the user's
    question.

ANSWER FORMAT:

Provide the answer first.

Use inline citations throughout.

Example:

LangGraph uses nodes and edges to represent workflow
operations and transitions. [1]

Then provide:

### Sources

[1] Source title — URL
[2] Source title — URL

The Sources section must contain ONLY successfully fetched
sources.
"""

    # ---------------------------------------------------------
    # FINAL MODEL
    # ---------------------------------------------------------
    model = create_tool_enabled_model()

    response = model.bind_tools([]).invoke(
        [
            SystemMessage(
                content=(
                    "You are an evidence-grounded research "
                    "answer writer. Use only the evidence "
                    "supplied in the user message."
                )
            ),
            HumanMessage(
                content=final_prompt
            ),
        ]
    )

    answer = response.content

    # ---------------------------------------------------------
    # HARD LIMIT NOTICE
    # ---------------------------------------------------------
    if limit_reached:

        source_word = (
            "source"
            if source_count == 1
            else "sources"
        )

        answer = (
            "The research agent reached its hard step limit. "
            f"The answer below is based only on the "
            f"{source_count} {source_word} successfully fetched "
            f"before the limit was reached.\n\n"
            + answer
        )

    return {
        "final_answer": answer,
        "status": (
            "limit_reached"
            if limit_reached
            else "completed"
        ),
    }


def route_after_agent(
    state: ResearchState,
) -> str:
    """
    Decide whether the graph should execute tools, continue
    researching, or finalize.
    """
    step_count = state.get(
        "step_count",
        0,
    )

    max_steps = state.get(
        "max_steps",
        6,
    )

    # Hard limit.
    if step_count >= max_steps:
        return "finish"

    message = _last_ai_message(
        state
    )

    # The model requested a tool.
    if message and message.tool_calls:
        return "tools"

    # We have verified evidence, so we can finalize.
    if state.get(
        "fetched_sources"
    ):
        return "finish"

    # No evidence yet. Continue researching.
    return "research"


def route_after_tools(
    state: ResearchState,
) -> str:
    """
    Return to the research agent after tool execution.
    """
    if (
        state.get("step_count", 0)
        >= state.get("max_steps", 6)
    ):
        return "finish"

    return "research"


def build_research_graph():
    """
    Build and compile the LangGraph research agent.
    """
    from langgraph.graph import (
        END,
        START,
        StateGraph,
    )

    graph = StateGraph(
        ResearchState
    )

    # Nodes
    graph.add_node(
        "research_agent",
        research_agent_node,
    )

    graph.add_node(
        "execute_tools",
        execute_tools_node,
    )

    graph.add_node(
        "finalize",
        finalize_node,
    )

    # Start
    graph.add_edge(
        START,
        "research_agent",
    )

    # Agent routing
    graph.add_conditional_edges(
        "research_agent",
        route_after_agent,
        {
            "tools": "execute_tools",
            "research": "research_agent",
            "finish": "finalize",
        },
    )

    # Tool routing
    graph.add_conditional_edges(
        "execute_tools",
        route_after_tools,
        {
            "research": "research_agent",
            "finish": "finalize",
        },
    )

    # Finish
    graph.add_edge(
        "finalize",
        END,
    )

    return graph.compile()