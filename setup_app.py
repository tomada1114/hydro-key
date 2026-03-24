"""py2app build configuration for HydroKey.app.

Patches ``parse_config_files`` to clear ``install_requires`` that
setuptools reads from ``pyproject.toml`` — py2app rejects it and we
bundle dependencies ourselves via the ``packages`` option.
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


def _patched_parse(self, *args, **kwargs):  # type: ignore[no-untyped-def]  # must match setuptools internal signature
    _orig_parse(self, *args, **kwargs)
    self.install_requires = []  # type: ignore[attr-defined]  # dynamically populated by setuptools


setuptools.dist.Distribution.parse_config_files = _patched_parse  # type: ignore[assignment]  # intentional monkey-patch for py2app compat

import py2app  # noqa: E402, F401, I001  # must import after monkey-patch; registers the py2app command with setuptools
from setuptools import setup  # type: ignore[import-untyped]  # noqa: E402  # py2app re-exports lack type info

_pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
_version: str = _pyproject["project"]["version"]

APP = ["src/hydro_key/_entry.py"]

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
        "NSAccessibilityUsageDescription": (
            "HydroKey needs accessibility access for global hotkeys."
        ),
    },
    "packages": ["hydro_key", "rumps", "pynput"],
    "includes": ["objc", "AppKit", "Foundation", "Quartz"],
}

if not _icon_path.exists():
    raise FileNotFoundError(
        f"Icon file not found: {_icon_path}. Run 'just icon' to generate it."
    )
OPTIONS["iconfile"] = str(_icon_path)

setup(
    name="HydroKey",
    app=APP,
    options={"py2app": OPTIONS},
)
