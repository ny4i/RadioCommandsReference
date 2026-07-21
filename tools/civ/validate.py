"""Refuse-by-default validation gate.

Emit markdown ONLY when every check passes. The catastrophic failure mode is
not a crash — it is well-formed-looking markdown with a subtly wrong byte that
then gets locked forever. So this gate proves well-formedness positively;
absence of an exception is never sufficient.

Bias: over-refuse. A false reject costs a human/LLM pass on one radio. A false
accept can lock in a command that keys a real transmitter.
"""
from dataclasses import dataclass, field

from .schema import CORE_COMMANDS


@dataclass
class Verdict:
    accepted: bool
    reason: str = ""                 # machine-routable: no-anchor|schema-mismatch|validation-failed:<check>|ok
    failures: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def validate(anchor, parse):
    """Return a Verdict. `anchor` is AnchorResult, `parse` is ParseResult."""
    failures, warnings = [], []

    if not anchor.found:
        return Verdict(False, "no-anchor", ["no CI-V frame signature located"])

    if not anchor.address:
        failures.append("no transceiver address extracted from frame")
    elif not anchor.address_consistent:
        warnings.append("address not confirmed by both frame directions")
    if anchor.address_known is False:
        warnings.append(anchor.notes[-1] if anchor.notes else "address disagrees with known table")

    if parse.tables_used == 0:
        return Verdict(False, "schema-mismatch",
                       ["no table matched the modern command-index schema "
                        "(likely older-cluster layout -> route to LLM)"])

    cmds = parse.commands
    if not cmds:
        failures.append("command-index table matched but yielded zero rows")

    # Every command byte must be valid hex (the parser guarantees this, but we
    # re-assert: a fused-row fragment would never have become a Command).
    bad = [c for c in cmds if not _is_hex(c.cmd)]
    if bad:
        failures.append(f"{len(bad)} rows have a non-hex command byte")

    # Core frequency commands must be present, else we did not capture the real
    # index (caught a partial/unrelated table).
    seen = {c.cmd for c in cmds}
    missing = CORE_COMMANDS - seen
    if missing:
        failures.append(f"core command(s) missing: {sorted(missing)}")

    # Duplicate (cmd, sub, subsub) keys. Two meanings:
    #  - a big cluster of dups whose Data cells are a sequential index => the
    #    radio uses a DEEPER (4-byte) menu address than our 3-level model can
    #    represent. Not corruption; route to LLM or extend the parser.
    #  - a small number of genuine collisions => real defect / fused rows.
    keys = [c.key() for c in cmds]
    dups = {k for k in keys if keys.count(k) > 1}
    if dups:
        if _looks_like_deep_menu(cmds, dups):
            return Verdict(False, "deep-menu-tree",
                           ["command uses a 4-byte menu address (e.g. 1A 05 gg ii); "
                            "3-level model cannot represent it -> route to LLM / extend parser"],
                           warnings)
        failures.append(f"{len(dups)} duplicate command keys")

    if failures:
        return Verdict(False, "validation-failed:" + failures[0].split(":")[0].replace(" ", "-")[:24],
                       failures, warnings)
    return Verdict(True, "ok", [], warnings)


def _looks_like_deep_menu(cmds, dups):
    """True if any duplicated key holds a large run of rows whose Data cells are
    a sequential 2-digit index — the signature of a 4-byte menu address."""
    import re
    for k in dups:
        data = [c.data for c in cmds if c.key() == k]
        idx = [d for d in data if re.fullmatch(r"[0-9A-Fa-f]{2}", d or "")]
        if len(idx) >= 8 and len(set(idx)) >= 8:
            return True
    return False


def _is_hex(tok):
    try:
        int(tok, 16)
        return len(tok) in (2, 4)
    except (TypeError, ValueError):
        return False
