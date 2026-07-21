"""Shared constants and text-normalization helpers for CI-V extraction.

Central place for the things every stage needs: the frame-format signature,
the command-table column schemas, and the byte-cleaning that undoes the
extraction gremlins observed across the corpus (U+FFFD for '.'/'-', doubled
glyphs, footnote markers glued to command bytes such as ``1A*`` / ``1A†``).
"""
import re

# --- Frame format (universal across every Icom manual seen) ---------------
# Controller -> radio:  FE FE <addr> E0 Cn Sc ... FD
# Radio -> controller:  FE FE E0 <addr> Cn Sc ... FD
FRAME_CTRL_TO_RADIO = re.compile(r"FE\s*FE\s*([0-9A-F]{2})\s*E0\s*Cn", re.I)
FRAME_RADIO_TO_CTRL = re.compile(r"FE\s*FE\s*E0\s*([0-9A-F]{2})\s*Cn", re.I)

# Documented CI-V default addresses. Used only as a soft cross-check; a
# mismatch is a warning (address is one templated byte, easy to human-verify),
# never a hard reject. Absence from this table is not an error.
KNOWN_ADDRESSES = {
    "IC-718": "5E",
    "IC-706": "58",
    "IC-756": "6E",
    "IC-7100": "88",
    "IC-7851": "8E",
    "IC-7850": "8E",
    "IC-7300": "94",
    "IC-9100": "7C",
}

# Core frequency/mode commands that MUST appear if we truly parsed the command
# index (not a fused or unrelated table). Their absence => refuse.
CORE_COMMANDS = {"00", "03", "05"}

# Column headers that identify a modern command-index table.
CMD_HEADER_TOKENS = ("cmd", "description")

_FFFD = "�"
_FOOTNOTE = "*†‡§¶"


def clean_cell(text):
    """Collapse whitespace and drop the U+FFFD replacement gremlin."""
    if text is None:
        return ""
    return " ".join(text.replace(_FFFD, "").split())


def as_byte(text):
    """Return an uppercased hex byte/word token, or None if the cell is not one.

    Strips trailing footnote markers (``1A*`` -> ``1A``). Accepts 2-char bytes
    and the 4-char sub-command codes newer radios use (``0023``).
    """
    t = clean_cell(text).rstrip(_FOOTNOTE).strip()
    if re.fullmatch(r"[0-9A-Fa-f]{2}", t) or re.fullmatch(r"[0-9A-Fa-f]{4}", t):
        return t.upper()
    return None


def has_footnote(text):
    """True if the raw cell carried a footnote marker (conditional command)."""
    return any(m in (text or "") for m in _FOOTNOTE)
