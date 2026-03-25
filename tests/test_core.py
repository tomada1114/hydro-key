"""Tests for the public hydro_key API."""

from __future__ import annotations

import importlib
import importlib.metadata as importlib_metadata
from importlib.metadata import PackageNotFoundError, version

import hydro_key
from hydro_key import __all__, __version__


class TestPackageMetadata:
    def test_public_exports(self):
        assert set(__all__) == {"__version__", "run"}

    def test_version_matches_installed_metadata(self):
        assert __version__ == version("hydro-key")

    def test_load_version_falls_back_to_normalized_name(self, monkeypatch):
        calls: list[str] = []

        def fake_version(distribution_name: str) -> str:
            calls.append(distribution_name)
            if distribution_name == "hydro-key":
                return "9.9.9"
            raise PackageNotFoundError(distribution_name)

        with monkeypatch.context() as patched:
            patched.setattr(importlib_metadata, "packages_distributions", dict)
            patched.setattr(importlib_metadata, "version", fake_version)
            reloaded = importlib.reload(hydro_key)

        assert reloaded.__version__ == "9.9.9"
        assert calls == ["hydro-key"]
        importlib.reload(hydro_key)

    def test_load_version_falls_back_to_local_pyproject(self, monkeypatch):
        def fake_version(_: str) -> str:
            raise PackageNotFoundError

        with monkeypatch.context() as patched:
            patched.setattr(importlib_metadata, "packages_distributions", dict)
            patched.setattr(importlib_metadata, "version", fake_version)
            reloaded = importlib.reload(hydro_key)

        assert reloaded.__version__ == "0.1.0"
        importlib.reload(hydro_key)

    def test_find_local_project_version_reads_pyproject(self, tmp_path):
        find_local_project_version = hydro_key.__dict__["_find_local_project_version"]
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text('[project]\nversion = "2.3.4"\n', encoding="utf-8")

        module_path = tmp_path / "src" / "demo" / "__init__.py"
        module_path.parent.mkdir(parents=True)
        module_path.write_text('"""demo"""', encoding="utf-8")

        assert find_local_project_version(module_path) == "2.3.4"

    def test_find_local_project_version_returns_none_without_pyproject(self, tmp_path):
        find_local_project_version = hydro_key.__dict__["_find_local_project_version"]
        module_path = tmp_path / "src" / "demo" / "__init__.py"
        module_path.parent.mkdir(parents=True)
        module_path.write_text('"""demo"""', encoding="utf-8")

        assert find_local_project_version(module_path) is None

    def test_find_local_project_version_returns_none_for_invalid_pyproject(
        self, tmp_path
    ):
        find_local_project_version = hydro_key.__dict__["_find_local_project_version"]
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text("[project\nversion = '2.3.4'\n", encoding="utf-8")

        module_path = tmp_path / "src" / "demo" / "__init__.py"
        module_path.parent.mkdir(parents=True)
        module_path.write_text('"""demo"""', encoding="utf-8")

        assert find_local_project_version(module_path) is None

    def test_find_local_project_version_returns_none_without_project_table(
        self, tmp_path
    ):
        find_local_project_version = hydro_key.__dict__["_find_local_project_version"]
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text("[build-system]\nrequires = []\n", encoding="utf-8")

        module_path = tmp_path / "src" / "demo" / "__init__.py"
        module_path.parent.mkdir(parents=True)
        module_path.write_text('"""demo"""', encoding="utf-8")

        assert find_local_project_version(module_path) is None

    def test_find_local_project_version_returns_none_without_version(self, tmp_path):
        find_local_project_version = hydro_key.__dict__["_find_local_project_version"]
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text("[project]\nname = 'demo'\n", encoding="utf-8")

        module_path = tmp_path / "src" / "demo" / "__init__.py"
        module_path.parent.mkdir(parents=True)
        module_path.write_text('"""demo"""', encoding="utf-8")

        assert find_local_project_version(module_path) is None

    def test_load_version_returns_unknown_without_installed_or_local_metadata(
        self, monkeypatch
    ):
        load_version = hydro_key.__dict__["_load_version"]

        def fake_version(_: str) -> str:
            raise PackageNotFoundError

        with monkeypatch.context() as patched:
            patched.setattr(hydro_key, "packages_distributions", dict)
            patched.setattr(hydro_key, "version", fake_version)
            patched.setattr(hydro_key, "_find_local_project_version", lambda: None)

            assert load_version() == "0.0.0+unknown"
