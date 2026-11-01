import json
from unittest.mock import Mock

import pytest
import requests
from txtai.pipeline import Pipeline

from desearch_txtai import Desearch, DesearchClient, DesearchError, DesearchTool, desearch_search
from desearch_txtai.pipeline import normalize


@pytest.fixture
def http(monkeypatch):
    response = Mock(status_code=200)
    response.json.return_value = {"data": [
        {"title": "Example", "link": "https://example.org", "snippet": "Details"},
        {"title": "Second", "url": "https://example.org/2"},
    ]}
    request = Mock(return_value=response)
    monkeypatch.setattr(requests, "request", request)
    monkeypatch.setenv("DESEARCH_API_KEY", "test-secret")
    return request, response


@pytest.mark.parametrize("mode,method,path,payload", [
    ("web", "GET", "/web", {"query": "hello", "start": 0}),
    ("ai", "POST", "/desearch/ai/search", {
        "prompt": "hello", "tools": DesearchClient.TOOLS, "count": 1,
        "streaming": False, "result_type": "LINKS_WITH_SUMMARIES",
    }),
    ("links", "POST", "/desearch/ai/search/links/web", {
        "prompt": "hello", "tools": ["web"], "count": 1,
    }),
    ("x", "GET", "/twitter", {"query": "hello", "count": 1, "sort": "Top"}),
])
def test_modes(http, mode, method, path, payload):
    request, _ = http
    pipeline = Desearch(timeout=7)
    assert isinstance(pipeline, Pipeline)
    assert pipeline("hello", mode, 1) == [
        {"title": "Example", "url": "https://example.org", "snippet": "Details"}
    ]
    request.assert_called_once_with(
        method, "https://api.desearch.ai" + path,
        headers={"Authorization": "Bearer test-secret"}, timeout=7,
        allow_redirects=False, **{"params" if method == "GET" else "json": payload},
    )


def test_batches(http):
    pipeline = Desearch()
    assert len(pipeline(["one", "two"])) == 2
    assert pipeline([]) == []
    assert http[0].call_count == 2


@pytest.mark.parametrize("key", ["data", "search_results", "results", "organic_results", "tweets"])
def test_envelopes(key):
    assert normalize({key: [{"link": "https://example.org", "text": "Post"}]}) == [
        {"title": "", "url": "https://example.org", "snippet": "Post"}
    ]
    assert normalize({"data": {key: [{"title": "Nested"}]}})[0]["title"] == "Nested"


@pytest.mark.parametrize("value", [None, "answer", {}, {"data": None}, [None, 4, {}]])
def test_empty_and_malformed_results(value):
    assert normalize(value) == []


def test_fallback_envelope():
    assert normalize({"data": [], "results": [{"title": "Fallback"}]})[0]["title"] == "Fallback"


def test_client_options(http):
    client = DesearchClient("explicit", timeout=9)
    client.web("query", start=20)
    assert http[0].call_args.kwargs["params"]["start"] == 20
    assert http[0].call_args.kwargs["headers"]["Authorization"] == "Bearer explicit"
    client.ai("query", result_type="LINKS_ONLY")
    assert http[0].call_args.kwargs["json"]["result_type"] == "LINKS_ONLY"


@pytest.mark.parametrize("status", [302, 401, 429, 500])
def test_http_errors(http, status):
    http[1].status_code = status
    http[1].text = "test-secret"
    with pytest.raises(DesearchError, match=f"HTTP {status}") as error:
        Desearch()("hello")
    assert "test-secret" not in str(error.value)


@pytest.mark.parametrize("exception,message", [
    (requests.Timeout("test-secret"), "timed out"),
    (requests.ConnectionError("test-secret"), "transport error"),
])
def test_transport_errors(http, exception, message):
    http[0].side_effect = exception
    with pytest.raises(DesearchError, match=message) as error:
        Desearch()("hello")
    assert "test-secret" not in str(error.value)
    assert error.value.__suppress_context__


def test_invalid_json(http):
    http[1].json.side_effect = ValueError("test-secret")
    with pytest.raises(DesearchError, match="invalid JSON"):
        Desearch()("hello")


def test_missing_key(monkeypatch):
    monkeypatch.delenv("DESEARCH_API_KEY", raising=False)
    with pytest.raises(ValueError, match="DESEARCH_API_KEY"):
        DesearchClient()


@pytest.mark.parametrize("kwargs,error", [
    ({"mode": "wrong"}, ValueError), ({"limit": 0}, ValueError),
    ({"limit": True}, ValueError), ({"limit": 1.5}, ValueError),
    ({"query": 42}, TypeError), ({"query": ["ok", 42]}, TypeError),
])
def test_invalid_inputs(http, kwargs, error):
    with pytest.raises(error):
        Desearch()(**{"query": "hello", **kwargs})
    http[0].assert_not_called()


def test_timeout_validation(http):
    with pytest.raises(ValueError, match="timeout"):
        DesearchClient(timeout=0)


def test_tools(http):
    expected = Desearch()("hello", limit=1)
    assert json.loads(desearch_search("hello", 1)) == expected
    assert json.loads(DesearchTool().search("hello", 1)) == expected


def test_agent_tool_factory(http):
    pytest.importorskip("smolagents")
    # Exercise txtai's actual conversion without downloading an LLM.
    from txtai.agent.tool.factory import ToolFactory

    tools = ToolFactory.create({"tools": [desearch_search, DesearchTool()]})
    for tool in tools:
        assert json.loads(tool(query="hello", limit=1))[0]["title"] == "Example"
