# HydroKey

[![CI](https://github.com/tomada1114/hydro-key/actions/workflows/ci.yml/badge.svg)](https://github.com/tomada1114/hydro-key/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/hydro-key)](https://pypi.org/project/hydro-key/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

macOS menu bar water intake tracker with global hotkey.

Press a hotkey to log each glass of water. HydroKey lives in your menu bar and
tracks your daily hydration progress toward a configurable goal.

## Requirements

- macOS 13+
- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Installation

```bash
git clone https://github.com/tomada1114/hydro-key.git
cd hydro-key
just install
```

Grant accessibility access for global hotkeys:
**System Settings → Privacy & Security → Accessibility** → add the `uv` binary
(typically `~/.local/bin/uv`).

## Usage

### Run manually

```bash
just run
# or
uv run hydrokey
```

### Auto-start on login

```bash
just install-agent    # Install macOS LaunchAgent (starts on login)
just agent-status     # Check if the agent is running
just uninstall-agent  # Remove the LaunchAgent
```

The LaunchAgent runs `uv run hydrokey` from the project directory.
If you move the project, re-run `just install-agent`.

Logs are written to:
- `~/Library/Logs/hydrokey.log`
- `~/Library/Logs/hydrokey.error.log`

## Development

```bash
just install  # Install dependencies and git hooks
just check    # Run all checks: format, lint, type check, tests
just test     # Run tests with coverage
just smoke    # Build and verify the wheel
```

## License

[MIT](LICENSE)
