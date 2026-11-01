"""txtai pipeline and response normalization."""

from txtai.pipeline import Pipeline

from .client import DesearchClient


def normalize(response):
    """Extract result records from common Desearch response envelopes."""
    if isinstance(response, list):
        records = response
    elif isinstance(response, dict):
        records = []
        for key in ("data", "search_results", "results", "organic_results", "tweets"):
            value = response.get(key)
            if isinstance(value, (list, dict)):
                records = normalize(value)
                if records:
                    return records
        return []
    else:
        return []

    output = []
    for item in records:
        if not isinstance(item, dict):
            continue
        def field(*names):
            return next((str(item[name]) for name in names if item.get(name) is not None), "")
        result = {
            "title": field("title", "name"),
            "url": field("url", "link", "tweet_url"),
            "snippet": field("snippet", "description", "text", "summary"),
        }
        if any(result.values()):
            output.append(result)
    return output


class Desearch(Pipeline):
    """Search Desearch and return dictionaries with title, url and snippet."""

    def __init__(self, api_key: str | None = None, timeout: float = 30):
        self.client = DesearchClient(api_key, timeout)

    def __call__(self, query: str | list[str], mode: str = "web", limit: int = 10):
        """Search one query or a list of queries, preserving the input shape.

        Web mode fetches the first page and returns up to limit results.
        Other modes send limit as the API count. No automatic pagination is used.
        """
        if mode not in ("web", "ai", "links", "x"):
            raise ValueError("mode must be web, ai, links or x.")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer.")
        if isinstance(query, list):
            if not all(isinstance(value, str) for value in query):
                raise TypeError("queries must be strings.")
            return [self(value, mode, limit) for value in query]
        if not isinstance(query, str):
            raise TypeError("query must be a string or list of strings.")
        response = self.client.web(query) if mode == "web" else getattr(self.client, mode)(query, limit)
        return normalize(response)[:limit]
