<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)"
            srcset="https://api.iconify.design/ri/scissors-line.svg?color=%23e6edf3&width=72&height=72" />
    <img src="https://api.iconify.design/ri/scissors-line.svg?color=%23222222&width=72&height=72" alt="" />
  </picture>
</p>

# ThinkStrip — Think-block filter for LLM streams

[![PyPI version](https://img.shields.io/pypi/v/thinkstrip.svg)](https://pypi.org/project/thinkstrip/)
[![Python versions](https://img.shields.io/pypi/pyversions/thinkstrip.svg)](https://pypi.org/project/thinkstrip/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/informity/thinkstrip/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/informity/thinkstrip/actions/workflows/ci.yml)

`thinkstrip` removes `<think>...</think>` blocks from model output in both batch and streaming
mode. It is designed for reasoning models (Qwen3, DeepSeek-R1, and others) that emit internal
reasoning before their visible answer.

The streaming case is the reason this package exists: tag boundaries can split across adjacent
token yields, so a correct implementation needs a stateful rolling buffer instead of a
post-generation regex.

---

## Why this exists

Reasoning models can emit output like:

```text
<think>hidden chain of thought</think>The actual answer.
```

For fully materialized strings, stripping is easy. For token streams, it is not. Partial tags
can arrive across multiple adjacent token yields, for example:

- `<thi` then `nk>`
- `</thi` then `nk>`

A naive `.replace()` or regex-per-token approach leaks fragments or drops visible output.
`thinkstrip` solves this with a stateful streaming filter.

---

## Install

Requirements:

- Python **3.13+**
- Zero runtime dependencies — installs and runs with nothing beyond the standard library

```bash
pip install thinkstrip
```

Development install:

```bash
pip install -e ".[dev]"
```

---

## Quick start

### Streaming

```python
from thinkstrip import ThinkStrip

stripper = ThinkStrip()
chunks   = []

for token in ['<thi', 'nk>', 'hidden', '</thi', 'nk>', 'The answer.']:
    if emitted := stripper.feed(token):
        chunks.append(emitted)

if flushed := stripper.flush():
    chunks.append(flushed)

print(''.join(chunks))
# The answer.
```

### Batch

```python
from thinkstrip import strip_think

clean = strip_think('<think>reasoning</think>The actual answer.')
print(clean)
# The actual answer.
```

### Prompt pre-cleaner

Some GGUF chat templates inject `<think>` at the end of the rendered prompt before
the model generates. This breaks the streaming filter because the model never emits
its own `<think>`. Call `strip_think_prefill` on the rendered prompt to remove it:

```python
from thinkstrip import strip_think_prefill

prompt = strip_think_prefill(prompt)
# trailing '<think>' removed if present; no-op otherwise
```

---

## Public API

```python
from thinkstrip import ThinkStrip, strip_think, strip_think_prefill
```

### `ThinkStrip`

Stateful streaming filter. Create one instance per response stream.

```python
ThinkStrip(
    open_tag:  str  = '<think>',
    close_tag: str  = '</think>',
    capture:   bool = False,
)
```

| Method / property | Description |
|---|---|
| `.feed(token: str) -> str` | Process one token. Returns the text to emit (empty string when nothing ready yet). |
| `.flush() -> str` | Call once at end-of-stream. Returns any buffered visible text. Empty if stream ended inside a think block. |
| `.reset() -> None` | Reset to initial state. Use to process a second stream with the same instance. |
| `.think_content: str` | Accumulated think-block text. Non-empty only when `capture=True`. |
| `.in_think_block: bool` | `True` if the stream ended mid-think-block. Useful for diagnostics. |

| Constructor parameter | Type | Default | Description |
|---|---|---|---|
| `open_tag` | `str` | `<think>` | Opening tag to strip |
| `close_tag` | `str` | `</think>` | Closing tag to strip |
| `capture` | `bool` | `False` | Retain think content in `.think_content` instead of discarding |

Buffer sizes are derived automatically: `len(open_tag) - 1` chars for the opening-tag guard,
`len(close_tag) - 1` for the closing-tag guard. Custom tags carry no extra cost.

### `strip_think`

Stateless helper for complete strings. Implemented via `ThinkStrip` — batch and streaming
behavior are identical.

```python
strip_think(
    text:      str,
    open_tag:  str = '<think>',
    close_tag: str = '</think>',
) -> str
```

### `strip_think_prefill`

Removes a trailing open tag injected by some GGUF chat templates.

```python
strip_think_prefill(
    prompt:   str,
    open_tag: str = '<think>',
) -> str
```

---

## Capture mode

When `capture=True`, think content accumulates in `.think_content` instead of being
discarded. Multiple think blocks per response are concatenated. Useful for surfacing
the model's reasoning in a separate UI panel or for eval runs.

```python
stripper = ThinkStrip(capture=True)

for token in stream:
    if emitted := stripper.feed(token):
        yield emitted

if flushed := stripper.flush():
    yield flushed

print(stripper.think_content)  # full reasoning text
```

---

## Limitations

- **Nested tags are not supported.** A `<think>` that arrives while already inside
  a think block is treated as think content and swallowed. The first `</think>` closes
  the block; any subsequent `</think>` with no matching open tag passes through as
  visible text. In practice this does not occur — Qwen3 and DeepSeek-R1 emit exactly
  one think block per response.

---

## Development

```bash
git clone https://github.com/informity/thinkstrip.git
cd thinkstrip

python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"

make lint
make test
make build
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](LICENSE).
