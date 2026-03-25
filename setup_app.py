"""py2app build configuration for HydroKey.app.

Patches ``parse_config_files`` to clear ``install_requires`` that
setuptools reads from ``pyproject.toml`` — py2app rejects it and we
bundle dependencies ourselves via the ``packages`` option.

The patch must be applied before ``py2app`` is imported because importing
``py2app`` registers the ``py2app`` command with setuptools, which triggers
config file parsing.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import setuptools.dist

if not hasattr(setuptools.dist.Distribution, "parse_config_files"):
    raise RuntimeError(
        "setuptools.dist.Distribution.parse_config_files not found. "
        "The py2app monkey-patch in setup_app.py is incompatible with this "
        f"version of setuptools ({setuptools.__version__}). "
        "Please update setup_app.py."
    )

_orig_parse = setuptools.dist.Distribution.parse_config_files


def _patched_parse(self, *args, **kwargs):  # type: ignore[no-untyped-def]
    _orig_parse(self, *args, **kwargs)
    self.install_requires = []  # type: ignore[attr-defined]


setuptools.dist.Distribution.parse_config_files = _patched_parse  # type: ignore[assignment]

import py2app  # noqa: E402, F401, I001  # must import after monkey-patch
from setuptools import setup  # type: ignore[import-untyped]  # noqa: E402  # setuptools ships no py.typed marker

_version: str = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))[
    "project"
]["version"]

_icon_path = Path("resources/HydroKey.icns")
if not _icon_path.exists():
    raise FileNotFoundError(
        f"Icon file not found: {_icon_path}. Run 'just icon' to generate it."
    )

APP = ["src/hydro_key/_entry.py"]

OPTIONS: dict[str, object] = {
    "argv_emulation": False,
    "iconfile": str(_icon_path),
    "plist": {
        "CFBundleName": "HydroKey",
        "CFBundleDisplayName": "HydroKey",
        "CFBundleIdentifier": "com.tomada.hydrokey",
        "CFBundleVersion": _version,
        "CFBundleShortVersionString": _version,
        "LSUIElement": True,
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "13.0",
        "NSAccessibilityUsageDescription": (
            "HydroKey needs accessibility access for global hotkeys."
        ),
    },
    "packages": ["hydro_key", "rumps", "pynput"],
    "includes": ["objc", "AppKit", "Foundation", "Quartz"],
}

setup(
    name="HydroKey",
    app=APP,
    options={"py2app": OPTIONS},
)
