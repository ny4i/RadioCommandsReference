"""Orchestrate: load -> locate -> parse -> validate -> (emit | reject).

Returns one RadioOutcome per PDF. The gate decides script-vs-LLM; nothing
reaches markdown without an ACCEPT verdict.
"""
import os
from dataclasses import dataclass, field

import pdfplumber

from . import anchor as anchor_mod
from . import parse as parse_mod
from . import validate as validate_mod
from . import emit as emit_mod


@dataclass
class RadioOutcome:
    pdf: str
    model: str
    accepted: bool = False
    reason: str = ""
    address: str = None
    civ_pages: list = field(default_factory=list)
    n_commands: int = 0
    failures: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    markdown: str = None
    route: str = ""                  # "script" | "llm"


def _model_name(pdf_name):
    base = os.path.basename(pdf_name)
    for sep in ("_", "."):
        base = base.split(sep)[0]
    return base


def _load(pdf_path):
    """Return (per_page_text, per_page_tables). Tables are raw row-lists."""
    pages_text, pages_tables = [], []
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages:
            pages_text.append(p.extract_text() or "")
            try:
                pages_tables.append([t.extract() for t in p.find_tables()])
            except Exception:
                pages_tables.append([])
    return pages_text, pages_tables


def process(pdf_path, extracted_at=""):
    model = _model_name(pdf_path)
    pages_text, pages_tables = _load(pdf_path)

    anchor = anchor_mod.locate(pages_text, os.path.basename(pdf_path))
    outcome = RadioOutcome(pdf=os.path.basename(pdf_path), model=model)

    if not anchor.found:
        outcome.reason = "no-anchor"
        outcome.failures = anchor.notes
        outcome.route = "llm"
        return outcome

    outcome.address = anchor.address
    outcome.civ_pages = anchor.pages

    # Parse tables on the anchor pages plus a small window after (command
    # tables often continue past the frame-diagram page).
    lo = min(anchor.pages)
    hi = min(len(pages_tables), max(anchor.pages) + 12)
    window_tables = []
    for pi in range(lo, hi):
        window_tables.extend(pages_tables[pi])

    parse = parse_mod.parse_tables(window_tables)
    verdict = validate_mod.validate(anchor, parse)

    outcome.accepted = verdict.accepted
    outcome.reason = verdict.reason
    outcome.failures = verdict.failures
    outcome.warnings = verdict.warnings
    outcome.n_commands = len(parse.commands)

    if verdict.accepted:
        outcome.route = "script"
        page_range = f"{lo + 1}-{hi}"
        outcome.markdown = emit_mod.render(
            model, anchor, parse, os.path.basename(pdf_path),
            page_range, method="script", extracted_at=extracted_at,
            verified=False,
        )
    else:
        outcome.route = "llm"
    return outcome
