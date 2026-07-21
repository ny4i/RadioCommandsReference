# Radio Commands Reference

This repo is for documentation. The intent is that the radio command set from various source material (typically the radio manual or radio programming guide) is converted to markdown by an external process.

The markdown can then be ingested by an AI agent for programming of the radio interface in various projects.

Note this repo makes no attempt to create any code to actually interface to a radio. This is purely a source of common documentation in agent-usable form.

## Organization

References are grouped by manufacturer, one folder per brand, with one markdown file per radio model:

```
Icom/
  IC-718-CIV-protocol.md
```

When adding a new radio:

- Place it under its manufacturer folder (create the folder if it does not exist), e.g. `Yaesu/`, `Kenwood/`.
- Name the file for the model and protocol, e.g. `<model>-<protocol>-protocol.md`.
- Keep one radio per file.

## Source material

Source PDFs (manuals, programming guides) are the input to the external conversion process, not part of the tracked reference set. They are ignored via `.gitignore` (`*.pdf` / `*.PDF`) — commit only the generated markdown.
