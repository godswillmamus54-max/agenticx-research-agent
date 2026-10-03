import os

from dotenv import load_dotenv


load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
MAX_STEPS = int(os.getenv("MAX_STEPS", "6"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))


def validate_config() -> None:
    """Validate required application configuration."""

    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not configured. "
            "Add it to the .env file."
        )

    if MAX_STEPS < 1:
        raise ValueError("MAX_STEPS must be at least 1.")

    if REQUEST_TIMEOUT < 1:
        raise ValueError("REQUEST_TIMEOUT must be at least 1.")