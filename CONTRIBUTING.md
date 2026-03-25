# Contributing to ThinkStrip

Thank you for your interest in contributing.

---

## Development setup

```bash
git clone https://github.com/informity/thinkstrip.git
cd thinkstrip

python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
```

---

## Running tests

```bash
pytest
```

---

## Linting and type checking

```bash
ruff check src/ tests/ examples/
mypy src/
```

All linter errors must be clean before opening a pull request.

---

## Building the package

```bash
python -m build
```

This produces `dist/thinkstrip-*.whl` and `dist/thinkstrip-*.tar.gz`.

---

## Branch and PR conventions

- Branch from `master` using the pattern `feat/short-description` or `fix/short-description`.
- Keep pull requests focused — one logical change per PR.
- All tests must pass and `ruff check` must be clean.
- Update `CHANGELOG.md` under `[Unreleased]` for any user-facing change.

---

## Public API contract

The public API surface is three symbols:

```python
from thinkstrip import ThinkStrip, strip_think, strip_think_prefill
```

- Do not rename or remove `ThinkStrip`, `strip_think`, or `strip_think_prefill` without a major version bump.
- Do not change the signature of `ThinkStrip.feed()`, `ThinkStrip.flush()`, or `ThinkStrip.reset()` without a minor version bump.
- Zero runtime dependencies must be maintained — no new entries in `[project.dependencies]`.

---

## Release process

1. Update `CHANGELOG.md`
2. Bump version in `pyproject.toml`
3. Commit to `master`
4. Create and push a tag like `v0.1.1`
5. GitHub Actions publishes to PyPI through Trusted Publishing
