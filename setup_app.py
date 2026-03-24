"""py2app build configuration for HydroKey.app.

Patches ``parse_config_files`` to clear ``install_requires`` that
setuptools reads from ``pyproject.toml`` — py2app rejects it and we
bundle dependencies ourselves via the ``packages`` option.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import setuptools.dist

_orig_parse = setuptools.dist.Distribution.parse_config_files


def _patched_parse(self, *args, **kwargs):  # type: ignore[no-untyped-def]
    _orig_parse(self, *args, **kwargs)
    self.install_requires = []  # type: ignore[attr-defined]


setuptools.dist.Distribution.parse_config_files = _patched_parse  # type: ignore[assignment]

import py2app  # noqa: E402, F401  # registers the py2app command
from setuptools import setup  # type: ignore[import-untyped]  # noqa: E402

_pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
_version: str = _pyproject["project"]["version"]

APP = ["src/hydro_key/_entry.py"]
DATA_FILES: list[str] = []

_icon_path = Path("resources/HydroKey.icns")

OPTIONS: dict[str, object] = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": "HydroKey",
        "CFBundleDisplayName": "HydroKey",
        "CFBundleIdentifier": "com.tomada.hydrokey",
        "CFBundleVersion": _version,
        "CFBundleShortVersionString": _version,
        "LSUIElement": True,
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "13.0",
        "NSAppleEventsUsageDescription": (
            "HydroKey needs accessibility access for global hotkeys."
        ),
    },
    "packages": ["hydro_key", "rumps", "pynput"],
    "includes": ["objc", "AppKit", "Foundation", "Quartz"],
}

if _icon_path.exists():
    OPTIONS["iconfile"] = str(_icon_path)

setup(
    name="HydroKey",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
)
