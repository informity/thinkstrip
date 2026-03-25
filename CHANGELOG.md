# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.1.0] — 2026-03-25

### Added

- `ThinkStrip` — stateful streaming filter; processes one token at a time via
  `.feed(token: str) -> str`; emits buffered visible text on `.flush() -> str` at
  end-of-stream; correctly handles `<think>` and `</think>` tags split across adjacent
  token yields using a rolling lookahead buffer
- `ThinkStrip.capture` constructor parameter — when `True`, accumulates think-block
  content in `.think_content` instead of discarding it; multiple think blocks per
  response are concatenated; useful for surfacing model reasoning in a separate UI panel
  or for eval runs
- `ThinkStrip.in_think_block` property — `True` when the stream ends mid-think-block
  (model output truncated before `</think>`); useful for diagnostics
- `ThinkStrip` custom tag support — `open_tag` and `close_tag` constructor parameters
  accept any non-empty string; lookahead buffer sizes are computed automatically from
  tag lengths so custom tags carry no extra cost
- `AsyncThinkStrip` — async wrapper around `ThinkStrip`; `await .feed()` and
  `await .flush()` delegate to `asyncio.to_thread()`; no threading primitives required
  by the caller
- `strip_think(text, open_tag, close_tag) -> str` — stateless batch helper; implemented
  via `ThinkStrip` so batch and streaming behavior are identical
- `strip_think_prefill(prompt, open_tag) -> str` — removes a trailing open tag injected
  by some GGUF chat templates before generation; prevents the streaming filter from
  missing the model-emitted `<think>` that would follow
- 72 tests across four test files:
  - `tests/test_stripper.py` — streaming, split-boundary, flush, capture, custom tags,
    malformed/truncated streams, nested tags, error handling, async
  - `tests/test_batch.py` — batch and prefill helpers, batch/streaming consistency
  - `tests/test_import.py` — public import smoke tests
  - `tests/test_properties.py` — property-based tests via `hypothesis` covering split
    invariance (500 examples), single-char splits, passthrough, idempotency, and
    capture round-trip
- GitHub Actions CI workflow — `ruff` lint + `pytest` on every push to `master` and
  on pull requests
- GitHub Actions publish workflow — tag-based PyPI trusted publishing on `v*.*.*` tags;
  no stored credentials required
- MIT license

---

[0.1.0]: https://github.com/informity/thinkstrip/releases/tag/v0.1.0
