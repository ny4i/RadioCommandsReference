# CI-V extractor (`tools/`)

Deterministic extractor that converts Icom CI-V command manuals (PDF) into the
reference markdown, and — critically — **flags anything it cannot process
instead of emitting silent garbage**.

## Usage

```bash
pip install -r tools/requirements.txt
python tools/extract_civ.py --src . --out output --write
```

- Scans `--src` for `*.pdf`, prints an accept/reject manifest, writes
  `manifest.json`, and (with `--write`) emits accepted markdown to
  `--out/Icom/<model>-CIV-protocol.md`.
- Exit code is non-zero if any PDF was rejected, so CI can gate on
  "everything either passed or is queued for the LLM path".

## How it works

1. **Locate** (`anchor.py`) — finds the CI-V section by the universal
   frame-format text (`FE FE <addr> E0 Cn … FD`), which is present in every
   Icom command manual regardless of era. Also derives the transceiver
   address, trusting it only when both frame directions agree.
2. **Parse** (`parse.py`) — extracts the labelled 4-col / 5-col command-index
   tables (modern cluster) via a row state machine that merges multi-row Data
   cells. Never guesses at other layouts.
3. **Validate** (`validate.py`) — **refuse-by-default gate**. Emits markdown
   only when every check passes (valid hex bytes, core freq commands present,
   no duplicate keys, address extracted). Biased to over-refuse.
4. **Emit** (`emit.py`) — markdown with provenance frontmatter
   (`source_pdf`, `page_range`, `method`, `verified`).

## Reject reasons (the LLM/human queue)

| reason | meaning | next step |
|---|---|---|
| `no-anchor` | no CI-V frame signature — wrong doc or non-Icom (e.g. Yaesu) | manual review |
| `schema-mismatch` | older-cluster layout (headerless, side-by-side lists) | LLM path |
| `deep-menu-tree` | 4-byte menu address (`1A 05 gg ii`) beyond the 3-level model | LLM path, or extend parser |
| `validation-failed:*` | a specific integrity check failed | inspect |

Accepted markdown is emitted with `verified: false`. It must pass human/round-trip
verification **before** being promoted into the tracked `Icom/` set and locked.

## Scope

Deterministic path currently covers the simpler-menu modern cluster
(e.g. IC-718, IC-7100, IC-9100). Deep-menu flagships (IC-7300 MkII, IC-905,
IC-7850) and older/other-manufacturer manuals are flagged for the LLM path.
Extending to a 4-level menu model would convert the deep-menu radios to
deterministic — tracked as the next increment.
