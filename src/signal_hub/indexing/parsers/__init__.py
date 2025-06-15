"""File parser framework for extracting meaningful chunks from code."""

from signal_hub.indexing.parsers.base import Parser, ParseError
from signal_hub.indexing.parsers.models import Chunk, ChunkType
from signal_hub.indexing.parsers.registry import ParserRegistry
from signal_hub.indexing.parsers.python import PythonParser
from signal_hub.indexing.parsers.javascript import JavaScriptParser
from signal_hub.indexing.parsers.markdown import MarkdownParser

__all__ = [
    "Parser",
    "ParseError",
    "Chunk",
    "ChunkType",
    "ParserRegistry",
    "PythonParser",
    "JavaScriptParser", 
    "MarkdownParser",
]