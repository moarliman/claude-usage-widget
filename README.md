# claude-usage-widget

A live terminal widget that shows your Claude Code monthly credit usage.

```
  Claude Code Usage

  $42.31 / $100.00    42.3% used
  █████████████████░░░░░░░░░░░░░░░░░░░░░░░

  Refreshes every 60s · Last updated 14:23:01 · Ctrl+C to exit
```

## Requirements

- macOS (reads the token from Keychain)
- [Claude Code](https://claude.ai/code) installed and signed in
- Python 3

## Usage

```bash
python widget.py
```

Refresh interval defaults to 60 seconds. To change it:

```bash
python widget.py --interval 30
```

## How it works

`fetch_usage.py` reads your Claude Code OAuth token from the macOS Keychain (`security find-generic-password`) and calls the Anthropic usage API. `widget.py` polls that on an interval and renders a color-coded bar chart directly in the terminal.

The bar turns yellow above 50% and red above 80%.
