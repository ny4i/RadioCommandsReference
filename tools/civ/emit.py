"""Render accepted commands to markdown with provenance frontmatter.

Provenance is mandatory: in years, you must be able to tell which files were
deterministically extracted vs LLM-produced, from which source and pages, and
whether a human has verified them.
"""
from .schema import KNOWN_ADDRESSES  # noqa: F401  (kept for downstream imports)


def _frame_block(address):
    a = address or "??"
    return (
        "## Frame Format\n\n"
        "```text\n"
        f"Controller to radio:  FE FE {a} E0 Cn Sc Data... FD\n"
        f"Radio to controller:  FE FE E0 {a} Cn Sc Data... FD\n"
        "OK response:          FE FE E0 " f"{a} FB FD\n"
        "NG response:          FE FE E0 " f"{a} FA FD\n"
        "```\n"
    )


def render(model, anchor, parse, source_pdf, page_range, method="script",
           extracted_at="", verified=False):
    """Return a markdown document string."""
    addr = anchor.address or "??"
    lines = []
    lines.append("---")
    lines.append(f"model: {model}")
    lines.append(f"protocol: Icom CI-V")
    lines.append(f"transceiver_address: {addr}")
    lines.append(f"source_pdf: {source_pdf}")
    lines.append(f"page_range: {page_range}")
    lines.append(f"method: {method}")
    lines.append(f"extracted_at: {extracted_at}")
    lines.append(f"verified: {str(verified).lower()}")
    lines.append("---\n")

    lines.append(f"# {model} CI-V Protocol\n")
    lines.append("## Overview\n")
    lines.append(f"- Protocol: Icom CI-V")
    lines.append(f"- Transceiver default address: `{addr}`")
    lines.append(f"- Controller default address: `E0`")
    lines.append(f"- Terminator: `FD`\n")

    lines.append(_frame_block(anchor.address))

    lines.append("\n## Commands\n")
    lines.append("| Cmd | Sub | Sub2 | Data | Description | Cond |")
    lines.append("|---|---|---|---|---|---|")
    for c in parse.commands:
        cond = "*" if c.conditional else ""
        desc = c.desc.replace("|", "\\|")
        lines.append(
            f"| `{c.cmd}` | {_code(c.sub)} | {_code(c.subsub)} | "
            f"{c.data or ''} | {desc} | {cond} |"
        )
    lines.append("")
    return "\n".join(lines)


def _code(v):
    return f"`{v}`" if v else ""
