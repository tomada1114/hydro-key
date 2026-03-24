"""HydroKey - macOS menu bar water intake tracker."""

from __future__ import annotations

import tomllib
from importlib.metadata import PackageNotFoundError, packages_distributions, version
from pathlib import Path


def _find_local_project_version(module_path: Path | None = None) -> str | None:
    """Return the local project version when importing directly from the source tree."""

    search_path = Path(__file__ if module_path is None else module_path).resolve()

    for parent in search_path.parents:
        pyproject_path = parent / "pyproject.toml"
        if not pyproject_path.is_file():
            continue

        try:
            pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            return None

        project = pyproject.get("project")
        if not isinstance(project, dict):
            return None

        version_value = project.get("version")
        if isinstance(version_value, str) and version_value:
            return version_value

        return None

    return None


def _load_version() -> str:
    """Return the installed distribution version for this package."""

    candidate_names = list(packages_distributions().get(__name__, []))
    candidate_names.extend([__name__.replace("_", "-"), __name__])

    for distribution_name in dict.fromkeys(candidate_names):
        try:
            return version(distribution_name)
        except PackageNotFoundError:
            continue

    local_version = _find_local_project_version()
    if local_version is not None:
        return local_version

    return "0.0.0+unknown"


def run() -> None:
    """Launch the HydroKey menu bar application."""
    from hydro_key._app import HydroKeyApp  # noqa: PLC0415  # defer GUI imports

    app = HydroKeyApp()
    app.run()


__version__ = _load_version()
__all__ = ["__version__", "run"]
