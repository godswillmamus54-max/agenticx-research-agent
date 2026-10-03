from typing import Any, Dict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from langchain_core.tools import tool

from app.config import REQUEST_TIMEOUT


@tool
def search_web(query: str) -> Dict[str, Any]:
    """
    Search the web and return structured search results.

    The search backend is intentionally hidden behind this tool so the
    research agent does not depend on a specific search provider.
    """

    query = query.strip()

    if not query:
        return {
            "ok": False,
            "query": query,
            "error": "Search query cannot be empty.",
            "results": [],
        }

    try:
        results = DDGS().text(
            query,
            max_results=5,
        )

        structured_results = []

        for result in results:
            title = result.get("title", "").strip()
            url = result.get("href", "").strip()
            snippet = result.get("body", "").strip()

            if not url:
                continue

            structured_results.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                }
            )

        if not structured_results:
            return {
                "ok": False,
                "query": query,
                "error": "Search completed but returned no usable results.",
                "results": [],
            }

        return {
            "ok": True,
            "query": query,
            "results": structured_results,
        }

    except Exception as exc:
        return {
            "ok": False,
            "query": query,
            "error": f"Search failed: {exc}",
            "results": [],
        }


@tool
def fetch_page(url: str) -> Dict[str, Any]:
    """
    Fetch a web page and extract readable text.
    """

    url = url.strip()

    if not url:
        return {
            "ok": False,
            "url": url,
            "error": "URL cannot be empty.",
            "text": "",
        }

    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        return {
            "ok": False,
            "url": url,
            "error": "URL must start with http:// or https://.",
            "text": "",
        }

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/154 Safari/537.36"
                )
            },
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for element in soup(
            [
                "script",
                "style",
                "noscript",
                "header",
                "footer",
                "nav",
            ]
        ):
            element.decompose()

        text = soup.get_text(
            separator=" ",
            strip=True,
        )

        text = text[:12000]

        if not text:
            return {
                "ok": False,
                "url": url,
                "error": "Page was fetched but no readable text was found.",
                "text": "",
            }

        return {
            "ok": True,
            "url": url,
            "title": soup.title.get_text(strip=True)
            if soup.title
            else "",
            "text": text,
        }

    except requests.RequestException as exc:
        return {
            "ok": False,
            "url": url,
            "error": f"Request failed: {exc}",
            "text": "",
        }

    except Exception as exc:
        return {
            "ok": False,
            "url": url,
            "error": f"Page extraction failed: {exc}",
            "text": "",
        }