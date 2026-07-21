"""Tests for the CI-V extractor.

Unit tests (no PDF) lock the risky logic: byte cleaning, the row state machine
(esp. multi-row Data merge), and the refuse-by-default gate. Integration tests
run against the corpus when present and SKIP otherwise, so CI stays green
without the gitignored PDFs.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from civ import schema, parse, validate, anchor  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
HDR4 = ["Cmd.", "Sub cmd.", "Data", "Description"]
HDR5 = ["Cmd.", "Sub cmd.", "", "Data", "Description"]


# --- schema.as_byte / clean_cell -----------------------------------------
def test_as_byte_strips_footnote_and_gremlin():
    assert schema.as_byte("1A*") == "1A"
    assert schema.as_byte("1A†") == "1A"
    assert schema.as_byte("0023") == "0023"
    assert schema.as_byte("Send freq") is None
    assert schema.as_byte("") is None


def test_clean_cell_drops_replacement_char():
    assert schema.clean_cell("See p� 5-5") == "See p 5-5"


# --- parse state machine --------------------------------------------------
def test_multirow_data_merges_not_duplicates():
    rows = [HDR5,
            ["1A", "05", "0055", "00", "Send/read setting"],
            ["", "", "", "01", ""]]              # pure Data continuation
    res = parse.parse_tables([rows])
    assert len(res.commands) == 1
    assert res.commands[0].key() == ("1A", "05", "0055")
    assert "01" in res.commands[0].data


def test_subsub_only_rows_are_distinct_keys():
    rows = [HDR5,
            ["1A", "05", "0023", "0000 to 0255", "a"],
            ["", "", "0024", "00 or 01", "b"],
            ["", "", "0025", "00 to 06", "c"]]
    res = parse.parse_tables([rows])
    keys = [c.key() for c in res.commands]
    assert keys == [("1A", "05", "0023"), ("1A", "05", "0024"), ("1A", "05", "0025")]


def test_carry_forward_command_byte():
    rows = [HDR4,
            ["07", "00", "", "Select VFO A"],
            ["", "01", "", "Select VFO B"]]
    res = parse.parse_tables([rows])
    assert [c.key() for c in res.commands] == [("07", "00", ""), ("07", "01", "")]


def test_non_command_table_ignored():
    rows = [["Menu", "Value"], ["Beep", "On"]]
    res = parse.parse_tables([rows])
    assert res.tables_used == 0 and res.commands == []


# --- validate gate --------------------------------------------------------
def _anchor(addr="5E"):
    return anchor.AnchorResult(found=True, pages=[0], address=addr,
                               address_consistent=True)


def test_reject_when_no_anchor():
    v = validate.validate(anchor.AnchorResult(found=False), parse.ParseResult())
    assert not v.accepted and v.reason == "no-anchor"


def test_reject_schema_mismatch():
    v = validate.validate(_anchor(), parse.ParseResult())  # no tables used
    assert not v.accepted and v.reason == "schema-mismatch"


def test_reject_missing_core_commands():
    pr = parse.ParseResult(tables_used=1,
                           commands=[parse.Command(cmd="00"), parse.Command(cmd="01")])
    v = validate.validate(_anchor(), pr)
    assert not v.accepted and "core" in v.reason


def test_reject_deep_menu_tree():
    cmds = [parse.Command(cmd="00"), parse.Command(cmd="03"), parse.Command(cmd="05")]
    for i in range(10):
        cmds.append(parse.Command(cmd="1A", sub="05", subsub="00",
                                  data=f"{i:02d}", desc="x"))
    pr = parse.ParseResult(tables_used=1, commands=cmds)
    v = validate.validate(_anchor(), pr)
    assert not v.accepted and v.reason == "deep-menu-tree"


def test_accept_clean_three_level():
    cmds = [parse.Command(cmd=c) for c in ("00", "03", "05", "06")]
    cmds.append(parse.Command(cmd="1A", sub="01", subsub="01", data="00 00 ~ 02 55"))
    pr = parse.ParseResult(tables_used=1, commands=cmds)
    v = validate.validate(_anchor(), pr)
    assert v.accepted and v.reason == "ok"


# --- integration against corpus (skip if PDFs absent) --------------------
def _has(name):
    return os.path.exists(os.path.join(ROOT, name))


@pytest.mark.skipif(not _has("IC-718_4487_ENG_AM_0.pdf"), reason="corpus PDF absent")
def test_ic718_accepts_and_matches_core():
    from civ import process
    o = process(os.path.join(ROOT, "IC-718_4487_ENG_AM_0.pdf"))
    assert o.accepted and o.address == "5E"
    assert o.n_commands > 50


@pytest.mark.skipif(not _has("FT-1000MP Operating Manual.pdf")
                    and not any("FT-1000MP" in f for f in os.listdir(ROOT)),
                    reason="Yaesu PDF absent")
def test_yaesu_is_flagged_not_crashed():
    from civ import process
    yaesu = [f for f in os.listdir(ROOT) if "FT-1000MP" in f and f.endswith(".pdf")]
    o = process(os.path.join(ROOT, yaesu[0]))
    assert not o.accepted and o.reason == "no-anchor" and o.route == "llm"
