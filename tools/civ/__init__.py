"""civ: deterministic Icom CI-V command-reference extractor.

Refuse-by-default. Emits markdown only for manuals whose command index parses
and validates cleanly; everything else is flagged and routed to the LLM path.
"""
from .pipeline import process, RadioOutcome  # noqa: F401
