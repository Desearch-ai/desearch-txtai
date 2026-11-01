# desearch-txtai

A small Desearch search pipeline and agent tool for txtai. Uses
[the Desearch API](https://api.desearch.ai). Python 3.10 or newer is required.

## Install

```bash
pip install desearch-txtai
# From this checkout:
pip install -e '.[test]'
```

## API key

```bash
export DESEARCH_API_KEY='your-api-key'
```

Get a key from Desearch. You can also pass `api_key` directly to `Desearch`,
`DesearchClient`, or `DesearchTool`. Keys are never included in package error
messages. Requests have a configurable timeout in seconds (default: 30).

## Pipeline

```python
from desearch_txtai import Desearch

search = Desearch(timeout=30)
print(search("semantic search", limit=5))
print(search(["vector search", "knowledge graphs"], mode="web", limit=3))
print(search("recent research on retrieval", mode="ai", limit=5))
print(search("semantic search documentation", mode="links", limit=5))
print(search("semantic search", mode="x", limit=5))
```

Each result has `title`, `url`, and `snippet` string fields. Missing fields
are empty strings. A string query returns a list of results; a list of queries
returns a list of result lists. Web mode fetches the first page and returns
up to `limit` results without automatic pagination. Other modes send `limit`
as the API count. Empty or unrecognized response envelopes return an empty list.

For raw responses, use `DesearchClient().web(query, start=0)`, `.ai(prompt,
count=10, result_type="LINKS_WITH_SUMMARIES")`, `.links(prompt, count=10)`, or
`.x(query, count=10)`. Failed requests raise `DesearchError` with the HTTP
status when available. Transport failures and invalid JSON also raise this error.

## Agent tool

Install txtai's agent dependencies first:

```bash
pip install 'desearch-txtai[agent]'
```

```python
from txtai import Agent
from desearch_txtai import DesearchTool, desearch_search

agent = Agent(
    tools=[desearch_search],
    llm="Qwen/Qwen3-0.6B",
    max_steps=5,
)
print(agent("Find sources explaining semantic search and cite their URLs."))

# Alternatively, configure a key and timeout on the helper:
tool = DesearchTool(timeout=60)  # Optional: api_key="your-api-key"
agent = Agent(tools=[tool], llm="Qwen/Qwen3-0.6B", max_steps=5)
```

Both tools accept `query` and optional `limit` (default: 5) and return a JSON
string of search results. Agent execution requires an LLM configured for your
environment and may download model weights.

## Tests

```bash
pytest
```

Unit tests mock HTTP and require no network. `tests/test_live.py` is skipped
unless `DESEARCH_API_KEY` is set; when enabled it makes a billable API request.

MIT licensed. Copyright 2026 Desearch.
