"""Parse modern-cluster command-index tables into structured commands.

Only handles the clean, labelled 4-col (`Cmd | Sub | Data | Description`) and
5-col (`Cmd | Sub | sub-sub | Data | Description`) schema. Anything that does
not present that schema is left for the validator to reject and route to the
LLM path — this module never guesses.

Row handling is a small state machine because a single logical command spans
multiple physical rows:
  * new command byte        -> start a new command, reset sub context
  * blank cmd, new sub/sub2 -> new entry under the carried command
  * blank cmd/sub/sub2      -> a Data continuation; MERGE into the prior entry
The last case is what previously produced empty-key duplicates.
"""
from dataclasses import dataclass, field

from .schema import CMD_HEADER_TOKENS, as_byte, clean_cell, has_footnote


@dataclass
class Command:
    cmd: str
    sub: str = ""
    subsub: str = ""
    data: str = ""
    desc: str = ""
    conditional: bool = False       # carried a footnote marker

    def key(self):
        return (self.cmd, self.sub, self.subsub)


@dataclass
class ParseResult:
    commands: list = field(default_factory=list)
    tables_seen: int = 0
    tables_used: int = 0
    notes: list = field(default_factory=list)


def _is_command_header(row):
    joined = " ".join(clean_cell(c).lower() for c in row)
    return all(tok in joined for tok in CMD_HEADER_TOKENS)


def _split_row(cells, ncol):
    """Return (raw_cmd, raw_sub, raw_subsub, data, desc) for 4- or 5-col rows."""
    cells = list(cells) + [""] * (ncol - len(cells))
    if ncol >= 5:
        return cells[0], cells[1], cells[2], cells[3], cells[4]
    return cells[0], cells[1], "", cells[2], cells[3]


def _parse_one_table(rows):
    ncol = max(len(r) for r in rows)
    out = []
    cur_cmd = cur_sub = None
    prev = None                      # last emitted Command, for data-merge
    for raw in rows[1:]:
        rc, rs, rss, data, desc = _split_row(raw, ncol)
        cmd_tok, sub_tok, subsub_tok = as_byte(rc), as_byte(rs), as_byte(rss)
        data, desc = clean_cell(data), clean_cell(desc)

        if not (cmd_tok or sub_tok or subsub_tok):
            # Pure Data continuation of the previous command.
            if prev is not None:
                if data:
                    prev.data = (prev.data + " / " + data).strip(" /")
                if desc and desc not in prev.desc:
                    prev.desc = (prev.desc + " " + desc).strip()
            continue

        if cmd_tok:
            cur_cmd = cmd_tok
            cur_sub = sub_tok or ""
        elif sub_tok:
            cur_sub = sub_tok
        # subsub-only rows leave cur_cmd/cur_sub intact

        if cur_cmd is None:
            continue                 # cannot anchor a command byte yet

        cmd = Command(
            cmd=cur_cmd,
            sub=cur_sub,
            subsub=subsub_tok or "",
            data=data,
            desc=desc,
            conditional=has_footnote(rc),
        )
        out.append(cmd)
        prev = cmd
    return out


def parse_tables(tables):
    """tables: list of raw row-lists (from pdfplumber .extract())."""
    res = ParseResult()
    for rows in tables:
        res.tables_seen += 1
        if not rows or len(rows) < 2 or not _is_command_header(rows[0]):
            continue
        if max(len(r) for r in rows) < 4:
            continue
        res.tables_used += 1
        res.commands.extend(_parse_one_table(rows))
    if res.tables_used == 0:
        res.notes.append("no table matched the modern command-index schema")
    return res
