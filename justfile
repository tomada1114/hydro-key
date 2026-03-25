# Development task runner — requires Just (https://just.systems)
# All commands also work without Just by running the uv commands directly.

# Show available recipes
default:
    @just --list

# Install dependencies and git hooks when available
install:
    uv sync --all-groups
    if git rev-parse --git-dir >/dev/null 2>&1; then uv run pre-commit install --install-hooks; else echo "Skipping pre-commit hook installation (not a Git repository)."; fi

# Alias for first-time project setup
setup: install

# Format code
fmt:
    uv run ruff format .
    uv run ruff check --fix .

# Run linters and type checker
lint:
    uv run ruff check .
    uv run ruff format --check .
    uv run mypy src scripts
    uv run vulture src/ --ignore-names "state,menu" --ignore-decorators "@rumps.*"

# Run tests with coverage
test:
    uv run pytest

# Run all checks: format, lint, test
check: fmt lint test

# Serve documentation locally
docs:
    uv run mkdocs serve

# Build distribution packages
build:
    uv build

# Build and smoke-test the wheel in a temporary virtual environment
smoke: build
    uv run python scripts/smoke_test.py

# Remove only py2app build artifacts (preserves tool caches)
clean-app:
    rm -rf dist/HydroKey.app build/

# Build macOS .app bundle using py2app
app: clean-app
    uv run python setup_app.py py2app

# Create .dmg installer from .app bundle
dmg: app
    rm -f dist/HydroKey.dmg
    hdiutil create -volname "HydroKey" \
        -srcfolder dist/HydroKey.app \
        -ov -format UDZO \
        dist/HydroKey.dmg

# Generate .icns icon from resources/icon.png (must be at least 1024x1024)
icon:
    @test -f resources/icon.png || (echo "Error: resources/icon.png not found" && exit 1)
    mkdir -p resources/HydroKey.iconset
    sips -z 16 16     resources/icon.png --out resources/HydroKey.iconset/icon_16x16.png
    sips -z 32 32     resources/icon.png --out resources/HydroKey.iconset/icon_16x16@2x.png
    sips -z 32 32     resources/icon.png --out resources/HydroKey.iconset/icon_32x32.png
    sips -z 64 64     resources/icon.png --out resources/HydroKey.iconset/icon_32x32@2x.png
    sips -z 128 128   resources/icon.png --out resources/HydroKey.iconset/icon_128x128.png
    sips -z 256 256   resources/icon.png --out resources/HydroKey.iconset/icon_128x128@2x.png
    sips -z 256 256   resources/icon.png --out resources/HydroKey.iconset/icon_256x256.png
    sips -z 512 512   resources/icon.png --out resources/HydroKey.iconset/icon_256x256@2x.png
    sips -z 512 512   resources/icon.png --out resources/HydroKey.iconset/icon_512x512.png
    sips -z 1024 1024 resources/icon.png --out resources/HydroKey.iconset/icon_512x512@2x.png
    iconutil -c icns resources/HydroKey.iconset -o resources/HydroKey.icns
    rm -rf resources/HydroKey.iconset

# Remove build artifacts
clean:
    rm -rf dist/ build/ .mypy_cache/ .ruff_cache/ .pytest_cache/ htmlcov/ .coverage site/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
