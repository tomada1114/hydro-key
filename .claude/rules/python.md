---
paths:
  - "src/**/*.py"
  - "scripts/**/*.py"
---

## Design

- Keep modules under 300 lines; one logical concern per module
- Keep functions under 40 lines; prefer 3 or fewer parameters (group related params with dataclass or TypedDict)
- Google-style docstrings (Args/Returns/Raises) on all public functions; document *why*, not what the type signature already says; don't document obvious code

## Error Handling

- Define a package-level base exception; derive all specific errors from it
- Always chain exceptions with `raise XError(...) from original` to preserve context
- Never bare `except:`; catch the most specific exception possible
- Use `logging.exception()` in catch blocks (auto-includes traceback), never `logger.error(str(e))`
- Never swallow exceptions silently; if catching, handle meaningfully or re-raise
- Never use exceptions for control flow
- Return `None` or a sentinel only when the caller expects it; prefer raising for true errors

## Type System

- Prefer `@dataclass(frozen=True, slots=True)` for internal value objects
- Use Pydantic (`BaseModel`) only at serialization/deserialization boundaries
- Use `TypedDict` for structured dict shapes (API responses, config dicts)
- Use `Protocol` for structural subtyping instead of ABC when possible
- Avoid `Any`; when unavoidable, add a comment explaining why (e.g., `# Any: third-party lib has no stubs`)

## Type Safety Overrides

- `type: ignore` is allowed ONLY for third-party libraries that lack type stubs
- MUST specify the exact error code: `# type: ignore[misc]` not bare `# type: ignore`
- MUST include a brief justification: `# type: ignore[misc]  # rumps has no type stubs`
- Before adding `type: ignore`, first try to resolve through design changes (typed dicts, wrappers, Protocol)
- NEVER use `type: ignore` to bypass errors in your own code

## Suppression Comments (noqa)

- `# noqa` is allowed ONLY for intentional rule violations with documented reasons
- MUST specify the exact rule code: `# noqa: PLC0415` not bare `# noqa`
- Valid use cases: lazy imports (`PLC0415`), security-safe subprocess calls (`S603`)
- Before adding `# noqa`, verify the rule code is correct for the actual violation
- NEVER use `# noqa` to silence warnings you don't understand

## Third-Party Object Integrity

- NEVER monkey-patch attributes onto third-party library objects
- Use composition: maintain your own mapping dict instead of adding attributes to external instances
- Example: instead of `menu_item._value = 42`, use `self._values[menu_item.title] = 42`

## Performance

- Use generator expressions and `itertools` for large sequences; avoid materializing unnecessary lists
- Use `__slots__` on frequently instantiated classes (dataclass `slots=True`)
- Use `functools.lru_cache` or `functools.cache` for expensive pure functions
- Prefer `str.join()` over `+=` concatenation in loops
- Use `collections.defaultdict`, `Counter`, `deque` instead of hand-rolled equivalents
- Avoid repeated attribute lookups in tight loops; bind to local variable
- Use `dict`/`set` for O(1) membership tests instead of lists
- Lazy-import heavy optional dependencies inside functions to reduce import time

## Pythonic Patterns

- EAFP (try/except) over LBYL (if-check) when dealing with duck typing or I/O
- Use context managers (`with`) for all resource management (files, connections, locks)
- Prefer comprehensions over `map()`/`filter()` for readability
- Use `enum.Enum` for fixed sets of values instead of string constants
- Use `walrus operator` (:=) for assign-and-test when it improves clarity
- Use structural pattern matching (`match/case`) for complex dispatch
- Use `*args` unpacking and `**kwargs` deliberately; avoid passing them blindly through call chains

## Security

- Never use `eval()`, `exec()`, or `pickle.loads()` on untrusted input
- Use `secrets` module for tokens/keys, not `random`
- Sanitize file paths to prevent directory traversal (`pathlib.Path.resolve()` then check prefix)

## Constants and Naming

- Use `UPPER_SNAKE_CASE` named constants instead of magic numbers/strings
- Boolean variables/params: prefix with `is_`, `has_`, `can_`, `should_`
- Private helpers: prefix with `_`; reserve `__` (name mangling) only for avoiding conflicts in subclass hierarchies
