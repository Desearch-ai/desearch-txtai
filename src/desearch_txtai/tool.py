"""Functions usable directly in txtai Agent tools lists."""

import json

from .pipeline import Desearch


def desearch_search(query: str, limit: int = 5) -> str:
    """Search the web with Desearch for sources relevant to a question.

    Args:
        query: Search terms or a natural language question.
        limit: Maximum number of results to return, a positive integer.

    Returns:
        JSON array of results containing title, url and snippet, or [] when empty.
    """
    return json.dumps(Desearch()(query, limit=limit), ensure_ascii=False)


class DesearchTool(dict):
    """Tool configuration for Agent(tools=[DesearchTool(api_key=...)])."""

    def __init__(self, api_key: str | None = None, timeout: float = 30):
        self.pipeline = Desearch(api_key, timeout)
        super().__init__(name="desearch_search", target=self.search)

    def search(self, query: str, limit: int = 5) -> str:
        """Search the web with Desearch for relevant sources.

        Args:
            query: Search terms or a natural language question.
            limit: Maximum number of results to return, a positive integer.

        Returns:
            JSON array of results with title, url and snippet.
        """
        return json.dumps(self.pipeline(query, limit=limit), ensure_ascii=False)
