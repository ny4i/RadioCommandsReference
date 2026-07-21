# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A documentation-only reference set. Radio command sets from source material (manuals, programming guides) are converted to markdown by an external process (e.g. an LLM), so that AI agents can ingest them when programming radio interfaces in other projects.

There is no build, lint, or test tooling — and no code that talks to a radio. The deliverable is the markdown itself. Treat correctness and fidelity to the source protocol as the bar, not software concerns.

## Organization

- Grouped by manufacturer: one folder per brand (`Icom/`, `Yaesu/`, …), one markdown file per radio model.
- File naming: `<model>-<protocol>-protocol.md` (e.g. `Icom/IC-718-CIV-protocol.md`).
- One radio per file. Create the manufacturer folder if it does not exist yet.

## Source PDFs

Source PDFs are conversion *inputs*, not tracked content. `.gitignore` excludes `*.pdf` / `*.PDF`; they stay local. Commit only the generated markdown.

## Protocol reference conventions (CI-V documents)

The IC-718 file is the reference template for structure. A CI-V protocol document is expected to cover:

- **Overview** — protocol name, transceiver/controller addresses, terminator, OK/NG responses. Note that framing conventions (preamble `FE FE`, `FD` terminator) are common across a manufacturer's CI-V radios, but addresses and command specifics differ per model — do not copy addresses between models.
- **Frame format** — controller→radio and radio→controller byte layouts.
- **Common encodings** — booleans, operating modes, and payload formats (e.g. 5-byte packed-decimal BCD frequency, least-significant-digit first).
- **Commands** — grouped tables with columns: Name, Cmd, Sub/Path, Direction, Data/Values.
- **Format details** — YAML blocks pinning down multi-byte payload byte order and value maps.

When adding or editing a document, keep hex byte values, command/subcommand codes, and value ranges verbatim from the source — these are consumed programmatically downstream, so a transcription error becomes a wrong radio command.
