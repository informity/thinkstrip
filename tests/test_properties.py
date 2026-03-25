# thinkstrip | Property-based tests — split invariance and output correctness
# Maintainer: Informity

# Core property under test:
#   For any text with think blocks, splitting it into tokens at arbitrary positions
#   always produces the same visible output as strip_think(text).
#
# This property cannot be exhausted by hand-crafted token lists. Hypothesis explores
# the full split-position space, including degenerate splits (single chars, empty
# tokens, splits exactly on tag boundaries) that are unlikely to be written by hand.

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from thinkstrip import ThinkStrip, strip_think

# ==============================================================================
# Strategies
# ==============================================================================

# Characters that will never accidentally form a <think> or </think> tag.
# Used for the "visible" and "think content" portions of structured inputs.
_SAFE_ALPHABET = (
    'abcdefghijklmnopqrstuvwxyz'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    '0123456789 .,!?\n\t'
)

_safe_text = st.text(alphabet=_SAFE_ALPHABET, max_size=80)


@st.composite
def _text_with_think_blocks(draw: st.DrawFn) -> str:
    # Build: [visible] (<think>[think]</think> [visible])...
    # n_blocks=0 → plain text with no think blocks.
    n_blocks = draw(st.integers(min_value=0, max_value=3))
    parts: list[str] = []
    for i in range(n_blocks + 1):
        parts.append(draw(_safe_text))
        if i < n_blocks:
            think = draw(_safe_text)
            parts.append(f'<think>{think}</think>')
    return ''.join(parts)


@st.composite
def _splits_of(draw: st.DrawFn, text: str) -> list[str]:
    # Partition text into chunks at arbitrary positions.
    n = len(text)
    if n == 0:
        return ['']
    # Draw up to min(n, 40) split points; deduplicate and sort.
    raw = draw(st.lists(st.integers(min_value=0, max_value=n), max_size=min(n, 40)))
    points = sorted({0, *raw, n})
    return [text[points[i]:points[i + 1]] for i in range(len(points) - 1)]


@st.composite
def _text_and_splits(draw: st.DrawFn) -> tuple[str, list[str]]:
    text   = draw(_text_with_think_blocks())
    chunks = draw(_splits_of(text))
    return text, chunks


# ==============================================================================
# Property: split invariance
# ==============================================================================

@given(_text_and_splits())
@settings(max_examples=500)
def test_split_invariance(text_and_chunks: tuple[str, list[str]]) -> None:
    # The core property: streaming any split of a text produces the same visible
    # output as batch strip_think on the full text.
    text, chunks = text_and_chunks

    stripper = ThinkStrip()
    streamed: list[str] = []
    for chunk in chunks:
        if emitted := stripper.feed(chunk):
            streamed.append(emitted)
    if flushed := stripper.flush():
        streamed.append(flushed)

    assert ''.join(streamed) == strip_think(text)


@given(_text_with_think_blocks())
@settings(max_examples=300)
def test_single_char_split_matches_batch(text: str) -> None:
    # Extreme case: one character per token — maximises boundary exposure.
    stripper = ThinkStrip()
    streamed: list[str] = []
    for ch in text:
        if emitted := stripper.feed(ch):
            streamed.append(emitted)
    if flushed := stripper.flush():
        streamed.append(flushed)

    assert ''.join(streamed) == strip_think(text)


# ==============================================================================
# Property: passthrough for tag-free text
# ==============================================================================

@given(_safe_text)
@settings(max_examples=300)
def test_tag_free_text_passes_through_unchanged(text: str) -> None:
    # Text with no think tags must be returned exactly as-is.
    assert strip_think(text) == text


@given(st.data())
@settings(max_examples=300)
def test_tag_free_text_streaming_passthrough(data: st.DataObject) -> None:
    text   = data.draw(_safe_text)
    chunks = data.draw(_splits_of(text))

    stripper = ThinkStrip()
    out: list[str] = []
    for chunk in chunks:
        if emitted := stripper.feed(chunk):
            out.append(emitted)
    if flushed := stripper.flush():
        out.append(flushed)

    assert ''.join(out) == text


# ==============================================================================
# Property: output never contains raw think tags
# ==============================================================================

@given(_text_with_think_blocks())
@settings(max_examples=300)
def test_output_never_contains_open_tag(text: str) -> None:
    assert '<think>' not in strip_think(text)


@given(_text_with_think_blocks())
@settings(max_examples=300)
def test_output_never_contains_close_tag(text: str) -> None:
    assert '</think>' not in strip_think(text)


# ==============================================================================
# Property: idempotency
# ==============================================================================

@given(_text_with_think_blocks())
@settings(max_examples=200)
def test_idempotent(text: str) -> None:
    # Stripping twice must equal stripping once.
    once  = strip_think(text)
    twice = strip_think(once)
    assert once == twice


# ==============================================================================
# Property: capture mode — think content is exactly what was between the tags
# ==============================================================================

@given(
    visible_before = _safe_text,
    think          = _safe_text,
    visible_after  = _safe_text,
)
@settings(max_examples=300)
def test_capture_think_content_single_block(
    visible_before: str,
    think:          str,
    visible_after:  str,
) -> None:
    text = f'{visible_before}<think>{think}</think>{visible_after}'

    stripper = ThinkStrip(capture=True)
    out: list[str] = []
    for ch in text:
        if emitted := stripper.feed(ch):
            out.append(emitted)
    if flushed := stripper.flush():
        out.append(flushed)

    assert ''.join(out)         == visible_before + visible_after
    assert stripper.think_content == think


@given(
    v1    = _safe_text,
    t1    = _safe_text,
    v2    = _safe_text,
    t2    = _safe_text,
    v3    = _safe_text,
)
@settings(max_examples=200)
def test_capture_think_content_two_blocks(
    v1: str,
    t1: str,
    v2: str,
    t2: str,
    v3: str,
) -> None:
    text = f'{v1}<think>{t1}</think>{v2}<think>{t2}</think>{v3}'

    stripper = ThinkStrip(capture=True)
    out: list[str] = []
    for ch in text:
        if emitted := stripper.feed(ch):
            out.append(emitted)
    if flushed := stripper.flush():
        out.append(flushed)

    assert ''.join(out)         == v1 + v2 + v3
    assert stripper.think_content == t1 + t2


# ==============================================================================
# Property: custom tags obey the same split invariance
# ==============================================================================

@given(
    visible = _safe_text,
    think   = _safe_text,
    data    = st.data(),
)
@settings(max_examples=200)
def test_custom_tags_split_invariance(
    visible: str,
    think:   str,
    data:    st.DataObject,
) -> None:
    open_tag  = '[REASON]'
    close_tag = '[/REASON]'
    text      = f'{open_tag}{think}{close_tag}{visible}'
    chunks    = data.draw(_splits_of(text))

    stripper = ThinkStrip(open_tag=open_tag, close_tag=close_tag)
    out: list[str] = []
    for chunk in chunks:
        if emitted := stripper.feed(chunk):
            out.append(emitted)
    if flushed := stripper.flush():
        out.append(flushed)

    assert ''.join(out) == visible
