from app.config import MAX_STEPS, validate_config
from app.graph import build_research_graph
from app.nodes import build_research_messages


def main() -> None:
    validate_config()

    question = input("\nResearch question: ").strip()

    if not question:
        print("No research question provided.")
        return

    graph = build_research_graph()

    initial_state = {
        "question": question,
        "messages": build_research_messages(question),
        "step_count": 0,
        "max_steps": MAX_STEPS,
        "next_action": None,
        "action_input": None,
        "tool_calls": [],
        "tool_results": [],
        "discovered_sources": [],
        "fetched_sources": [],
        "sources": [],
        "errors": [],
        "pending_fetches": 0,
        "final_answer": None,
        "status": "running",
    }

    print("\nStarting research agent...")
    print(f"Question: {question}")
    print(f"Maximum steps: {MAX_STEPS}")

    result = graph.invoke(initial_state)

    print("\n" + "=" * 60)
    print("RESEARCH RESULT")
    print("=" * 60)

    print(f"STATUS: {result.get('status')}")
    print(f"STEPS: {result.get('step_count', 0)}")
    print(f"TOOL CALLS: {len(result.get('tool_calls', []))}")
    print(f"TOOL RESULTS: {len(result.get('tool_results', []))}")
    print(f"DISCOVERED SOURCES: {len(result.get('discovered_sources', []))}")
    print(f"FETCHED SOURCES: {len(result.get('fetched_sources', []))}")
    print(f"ERRORS: {len(result.get('errors', []))}")

    if result.get("errors"):
        print("\nERRORS:")
        for error in result["errors"]:
            print(f"- {error}")

    print("\nFINAL ANSWER:")
    print(result.get("final_answer") or "No final answer produced.")


if __name__ == "__main__":
    main()