from langchain_openai import ChatOpenAI

from app.config import MODEL_NAME, OPENAI_API_KEY
from app.prompts import SYSTEM_PROMPT
from app.tools import fetch_page, search_web


def create_research_model() -> ChatOpenAI:
    """Create the OpenAI chat model used by the research agent."""

    return ChatOpenAI(
        model=MODEL_NAME,
        api_key=OPENAI_API_KEY,
        temperature=0,
    )


def create_tool_enabled_model() -> ChatOpenAI:
    """Create the research model with the available tools bound."""

    model = create_research_model()

    return model.bind_tools(
        [
            search_web,
            fetch_page,
        ]
    )


def build_research_messages(question: str) -> list:
    """Build the initial messages for a research run."""

    return [
        ("system", SYSTEM_PROMPT),
        ("human", question),
    ]