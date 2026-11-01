"""Small HTTP client for the Desearch API."""

import os

import requests


class DesearchError(RuntimeError):
    """An API request failed."""


class DesearchClient:
    """Authenticate with an explicit key or DESEARCH_API_KEY."""

    BASE_URL = "https://api.desearch.ai"
    TOOLS = ["web", "twitter", "arxiv", "wikipedia", "hackernews", "reddit"]

    def __init__(self, api_key: str | None = None, timeout: float = 30):
        key = api_key if api_key is not None else os.getenv("DESEARCH_API_KEY")
        if not key or not key.strip():
            raise ValueError("Set DESEARCH_API_KEY or pass api_key.")
        if timeout <= 0:
            raise ValueError("timeout must be positive.")
        self._api_key = key
        self.timeout = timeout

    def _request(self, method, path, **kwargs):
        # Never include response bodies, request headers or transport exceptions in errors.
        try:
            response = requests.request(
                method, self.BASE_URL + path,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=self.timeout, allow_redirects=False, **kwargs,
            )
        except requests.Timeout:
            raise DesearchError("Desearch request timed out.") from None
        except requests.RequestException:
            raise DesearchError("Desearch request failed (connection or transport error).") from None
        if not 200 <= response.status_code < 300:
            raise DesearchError(f"Desearch API returned HTTP {response.status_code}.")
        try:
            return response.json()
        except ValueError:
            raise DesearchError("Desearch API returned invalid JSON.") from None

    def web(self, query: str, start: int = 0):
        """Search the web, starting at the supplied result offset."""
        return self._request("GET", "/web", params={"query": query, "start": start})

    def ai(self, prompt: str, count: int = 10, result_type: str = "LINKS_WITH_SUMMARIES"):
        """Search all supported sources without streaming."""
        return self._request("POST", "/desearch/ai/search", json={
            "prompt": prompt, "tools": self.TOOLS.copy(), "count": count,
            "streaming": False, "result_type": result_type,
        })

    def links(self, prompt: str, count: int = 10):
        """Search for web links."""
        return self._request("POST", "/desearch/ai/search/links/web", json={
            "prompt": prompt, "tools": ["web"], "count": count,
        })

    def x(self, query: str, count: int = 10):
        """Search X posts, sorted by Top."""
        return self._request("GET", "/twitter", params={
            "query": query, "count": count, "sort": "Top",
        })
