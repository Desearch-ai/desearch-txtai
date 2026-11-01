"""Opt-in smoke test; makes an actual API request when a key is present."""

import os

import pytest

from desearch_txtai import Desearch


@pytest.mark.skipif(not os.getenv("DESEARCH_API_KEY"), reason="DESEARCH_API_KEY is not set")
def test_live_web():
    results = Desearch()("txtai semantic search", limit=2)
    assert results
    assert len(results) <= 2
    assert all(set(result) == {"title", "url", "snippet"} for result in results)
    assert any(result["url"].startswith("http") for result in results)
