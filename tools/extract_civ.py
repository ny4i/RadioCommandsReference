#!/usr/bin/env python3
"""CLI: run the CI-V extractor over a directory of Icom manual PDFs.

  python tools/extract_civ.py [--src .] [--out output] [--write]

Prints a per-radio accept/reject manifest, writes manifest.json, and (with
--write) emits accepted markdown into --out. Rejected radios are listed with a
machine-routable reason for the LLM queue. Exit code is non-zero if any PDF was
rejected, so CI can gate on "everything either passed or is queued".
"""
import argparse
import datetime as _dt
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from civ import process  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=".", help="directory to scan for *.pdf")
    ap.add_argument("--out", default="output", help="markdown output directory")
    ap.add_argument("--write", action="store_true", help="write accepted markdown")
    args = ap.parse_args()

    stamp = _dt.datetime.now().strftime("%Y-%m-%d")
    pdfs = sorted(glob.glob(os.path.join(args.src, "*.pdf")) +
                  glob.glob(os.path.join(args.src, "*.PDF")))
    if not pdfs:
        print(f"no PDFs found in {args.src}", file=sys.stderr)
        return 2

    manifest, n_accept, n_reject = [], 0, 0
    print(f"{'RADIO':<16} {'VERDICT':<8} {'ADDR':<5} {'CMDS':>5}  REASON / WARNINGS")
    print("-" * 78)
    for pdf in pdfs:
        o = process(pdf, extracted_at=stamp)
        verdict = "ACCEPT" if o.accepted else "REJECT"
        n_accept += o.accepted
        n_reject += not o.accepted
        note = "" if o.accepted else o.reason
        if o.warnings:
            note = (note + "  ⚠ " + "; ".join(o.warnings)).strip()
        print(f"{o.model:<16} {verdict:<8} {str(o.address or '-'):<5} "
              f"{o.n_commands:>5}  {note}")
        for f in (o.failures or []):
            print(f"{'':<16} └─ {f}")

        if o.accepted and args.write:
            os.makedirs(os.path.join(args.out, "Icom"), exist_ok=True)
            path = os.path.join(args.out, "Icom", f"{o.model}-CIV-protocol.md")
            with open(path, "w") as fh:
                fh.write(o.markdown)

        manifest.append({
            "pdf": o.pdf, "model": o.model, "accepted": o.accepted,
            "reason": o.reason, "route": o.route, "address": o.address,
            "civ_pages": o.civ_pages, "n_commands": o.n_commands,
            "failures": o.failures, "warnings": o.warnings,
        })

    with open(os.path.join(args.out if args.write else ".", "manifest.json"), "w") as fh:
        json.dump({"generated": stamp, "radios": manifest}, fh, indent=2)

    print("-" * 78)
    print(f"accepted (script): {n_accept}   rejected (-> LLM): {n_reject}")
    return 1 if n_reject else 0


if __name__ == "__main__":
    sys.exit(main())
