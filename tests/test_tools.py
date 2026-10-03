from app.tools import fetch_page, search_web


def test_search_web_rejects_empty_query():
    result = search_web.invoke({"query": ""})

    assert result["ok"] is False
    assert "empty" in result["error"].lower()


def test_fetch_page_rejects_empty_url():
    result = fetch_page.invoke({"url": ""})

    assert result["ok"] is False
    assert "url" in result["error"].lower()


def test_fetch_page_rejects_invalid_url():
    result = fetch_page.invoke({"url": "not-a-url"})

    assert result["ok"] is False
    assert "http" in result["error"].lower()