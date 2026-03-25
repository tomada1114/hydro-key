"""Install / uninstall the HydroKey LaunchAgent for macOS login auto-start."""

from __future__ import annotations

import plistlib
import subprocess
import sys
from pathlib import Path

LABEL = "com.tomada.hydrokey"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
REPO_ROOT = Path(__file__).resolve().parents[1]


def _find_uv() -> str:
    """Return the absolute path to the uv binary."""

    result = subprocess.run(
        ["which", "uv"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()

    # Fallback: common install location
    fallback = Path.home() / ".local" / "bin" / "uv"
    if fallback.is_file():
        return str(fallback)

    msg = "Could not find uv binary. Please ensure uv is installed."
    raise SystemExit(msg)


def _build_plist() -> dict[str, object]:
    """Build the LaunchAgent plist dictionary."""

    uv_path = _find_uv()
    return {
        "Label": LABEL,
        "ProgramArguments": [uv_path, "run", "hydrokey"],
        "WorkingDirectory": str(REPO_ROOT),
        "RunAtLoad": True,
        "KeepAlive": False,
        "StandardOutPath": str(Path.home() / "Library" / "Logs" / "hydrokey.log"),
        "StandardErrorPath": str(
            Path.home() / "Library" / "Logs" / "hydrokey.error.log"
        ),
    }


def install() -> int:
    """Generate and install the LaunchAgent plist."""

    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)

    plist_data = _build_plist()
    with PLIST_PATH.open("wb") as f:
        plistlib.dump(plist_data, f)

    # Unload first if already loaded (ignore errors)
    subprocess.run(  # noqa: S603
        ["launchctl", "unload", str(PLIST_PATH)],  # noqa: S607
        capture_output=True,
        check=False,
    )
    subprocess.run(  # noqa: S603
        ["launchctl", "load", str(PLIST_PATH)],  # noqa: S607
        check=True,
    )

    sys.stdout.write(f"Installed and loaded: {PLIST_PATH}\n")
    sys.stdout.write(f"Working directory: {REPO_ROOT}\n")
    sys.stdout.write(f"uv path: {plist_data['ProgramArguments'][0]}\n")  # type: ignore[index]
    return 0


def uninstall() -> int:
    """Unload and remove the LaunchAgent plist."""

    if not PLIST_PATH.exists():
        sys.stdout.write(f"Not installed: {PLIST_PATH}\n")
        return 0

    subprocess.run(  # noqa: S603
        ["launchctl", "unload", str(PLIST_PATH)],  # noqa: S607
        capture_output=True,
        check=False,
    )
    PLIST_PATH.unlink()
    sys.stdout.write(f"Uninstalled: {PLIST_PATH}\n")
    return 0


def status() -> int:
    """Show whether the LaunchAgent is installed and loaded."""

    if not PLIST_PATH.exists():
        sys.stdout.write("Not installed.\n")
        return 1

    result = subprocess.run(
        ["launchctl", "list"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    loaded = any(LABEL in line for line in result.stdout.splitlines())
    state = "loaded" if loaded else "installed but not loaded"
    sys.stdout.write(f"{state}: {PLIST_PATH}\n")
    return 0


def main(arguments: list[str]) -> int:
    """Entry point: install, uninstall, or status."""

    if len(arguments) < 2 or arguments[1] not in {"install", "uninstall", "status"}:  # noqa: PLR2004
        sys.stderr.write("Usage: python launchagent.py {install|uninstall|status}\n")
        return 2

    commands = {"install": install, "uninstall": uninstall, "status": status}
    return commands[arguments[1]]()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
