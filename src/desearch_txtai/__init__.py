"""Desearch search integration for txtai."""

from .client import DesearchClient, DesearchError
from .pipeline import Desearch
from .tool import DesearchTool, desearch_search

__all__ = ["DesearchClient", "DesearchError", "Desearch", "DesearchTool", "desearch_search"]
__version__ = "0.1.0"
