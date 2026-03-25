# thinkstrip | Streaming filter tests — ThinkStrip and AsyncThinkStrip
# Maintainer: Informity

import pytest

from thinkstrip import AsyncThinkStrip, ThinkStrip

# ==============================================================================
# Helpers
# ==============================================================================

def _stream(tokens: list[str], capture: bool = False) -> tuple[str, str]:
    """Feed a token list through ThinkStrip and return (visible, think_content)."""
    stripper = ThinkStrip(capture=capture)
    out: list[str] = []

    for token in tokens:
        emitted = stripper.feed(token)
        if emitted:
            out.append(emitted)

    flushed = stripper.flush()
    if flushed:
        out.append(flushed)

    return ''.join(out), stripper.think_content


# ==============================================================================
# Basic visibility
# ==============================================================================

def test_no_think_block_passes_through() -> None:
    visible, _ = _stream(['Hello', ' world'])
    assert visible == 'Hello world'


def test_think_block_only_yields_nothing() -> None:
    visible, _ = _stream(['<think>hidden</think>'])
    assert visible == ''


def test_visible_before_think_block() -> None:
    visible, _ = _stream(['Prefix ', '<think>hidden</think>'])
    assert visible == 'Prefix '


def test_visible_after_think_block() -> None:
    visible, _ = _stream(['<think>hidden</think>', 'Suffix'])
    assert visible == 'Suffix'


def test_visible_before_and_after_think_block() -> None:
    visible, _ = _stream(['Hello ', '<think>secret</think>', ' world'])
    assert visible == 'Hello  world'


def test_empty_think_block() -> None:
    visible, _ = _stream(['<think></think>', 'Answer'])
    assert visible == 'Answer'


# ==============================================================================
# Split-tag boundary handling
# ==============================================================================

def test_open_tag_split_across_two_tokens() -> None:
    visible, _ = _stream(['<thi', 'nk>hidden</think>Answer'])
    assert visible == 'Answer'


def test_close_tag_split_across_two_tokens() -> None:
    visible, _ = _stream(['<think>hidden</thi', 'nk>Answer'])
    assert visible == 'Answer'


def test_both_tags_split_across_boundaries() -> None:
    visible, _ = _stream(['<thi', 'nk>', 'secret', '</thi', 'nk>', 'Visible'])
    assert visible == 'Visible'


def test_open_tag_split_across_three_tokens() -> None:
    visible, _ = _stream(['<', 'thi', 'nk>hidden</think>Answer'])
    assert visible == 'Answer'


def test_close_tag_split_across_three_tokens() -> None:
    visible, _ = _stream(['<think>hidden<', '/', 'think>Answer'])
    assert visible == 'Answer'


def test_single_char_tokens() -> None:
    tokens = list('<think>hidden</think>Answer')
    visible, _ = _stream(tokens)
    assert visible == 'Answer'


# ==============================================================================
# Multiple think blocks
# ==============================================================================

def test_two_think_blocks() -> None:
    visible, _ = _stream(['A<think>x</think>B<think>y</think>C'])
    assert visible == 'ABC'


def test_three_think_blocks_alternating() -> None:
    tokens = [
        'One', '<think>', 'r1', '</think>',
        'Two', '<think>', 'r2', '</think>',
        'Three',
    ]
    visible, _ = _stream(tokens)
    assert visible == 'OneTwoThree'


# ==============================================================================
# Flush behaviour
# ==============================================================================

def test_flush_preserves_partial_visible_tail() -> None:
    stripper = ThinkStrip()
    assert stripper.feed('Done') == ''
    assert stripper.flush() == 'Done'


def test_flush_returns_empty_when_in_think_block() -> None:
    stripper = ThinkStrip()
    stripper.feed('<think>unclosed')
    assert stripper.flush() == ''


def test_in_think_block_true_when_stream_ends_mid_think() -> None:
    stripper = ThinkStrip()
    stripper.feed('<think>never closed')
    stripper.flush()
    assert stripper.in_think_block is True


def test_in_think_block_false_after_close_tag() -> None:
    stripper = ThinkStrip()
    stripper.feed('<think>hidden</think>visible')
    stripper.flush()
    assert stripper.in_think_block is False


def test_partial_open_tag_at_end_flushed_as_visible() -> None:
    # '<thi' does not complete the open tag — must be emitted on flush
    stripper = ThinkStrip()
    stripper.feed('<thi')
    assert stripper.flush() == '<thi'


# ==============================================================================
# Capture mode
# ==============================================================================

def test_capture_mode_single_block() -> None:
    visible, think = _stream(['<think>reasoning</think>Answer'], capture=True)
    assert visible == 'Answer'
    assert think   == 'reasoning'


def test_capture_mode_split_tokens() -> None:
    visible, think = _stream(
        ['<thi', 'nk>', 'abc', 'def', '</thi', 'nk>', 'ok'],
        capture=True,
    )
    assert visible == 'ok'
    assert think   == 'abcdef'


def test_capture_mode_multiple_blocks_concatenated() -> None:
    visible, think = _stream(
        ['<think>r1</think>A<think>r2</think>B'],
        capture=True,
    )
    assert visible == 'AB'
    assert think   == 'r1r2'


def test_capture_mode_unclosed_block_captured_on_flush() -> None:
    stripper = ThinkStrip(capture=True)
    stripper.feed('<think>partial')
    stripper.flush()
    assert stripper.think_content == 'partial'


def test_capture_false_think_content_always_empty() -> None:
    visible, think = _stream(['<think>secret</think>Answer'], capture=False)
    assert visible == 'Answer'
    assert think   == ''


# ==============================================================================
# Custom tags
# ==============================================================================

def test_custom_open_and_close_tags() -> None:
    stripper = ThinkStrip(open_tag='[THINK]', close_tag='[/THINK]')
    out: list[str] = []

    for token in ['[THINK]', 'hidden', '[/THINK]', 'visible']:
        emitted = stripper.feed(token)
        if emitted:
            out.append(emitted)

    out.append(stripper.flush())
    assert ''.join(out) == 'visible'


def test_custom_tags_split_across_boundaries() -> None:
    stripper = ThinkStrip(open_tag='[THINK]', close_tag='[/THINK]')
    out: list[str] = []

    for token in ['[THI', 'NK]hidden[/THI', 'NK]visible']:
        emitted = stripper.feed(token)
        if emitted:
            out.append(emitted)

    out.append(stripper.flush())
    assert ''.join(out) == 'visible'


# ==============================================================================
# Error handling
# ==============================================================================

def test_type_error_on_non_string_token() -> None:
    stripper = ThinkStrip()
    with pytest.raises(TypeError, match='token must be a string'):
        stripper.feed(42)  # type: ignore[arg-type]


def test_value_error_on_empty_open_tag() -> None:
    with pytest.raises(ValueError, match='open_tag must not be empty'):
        ThinkStrip(open_tag='')


def test_value_error_on_empty_close_tag() -> None:
    with pytest.raises(ValueError, match='close_tag must not be empty'):
        ThinkStrip(close_tag='')


def test_empty_token_is_noop() -> None:
    stripper = ThinkStrip()
    assert stripper.feed('') == ''
    assert stripper.flush() == ''


# ==============================================================================
# AsyncThinkStrip
# ==============================================================================

async def test_async_basic_stream() -> None:
    stripper = AsyncThinkStrip()
    out: list[str] = []

    for token in ['<thi', 'nk>', 'hidden', '</thi', 'nk>', 'Answer']:
        emitted = await stripper.feed(token)
        if emitted:
            out.append(emitted)

    flushed = await stripper.flush()
    if flushed:
        out.append(flushed)

    assert ''.join(out) == 'Answer'


async def test_async_capture_mode() -> None:
    stripper = AsyncThinkStrip(capture=True)

    await stripper.feed('<think>')
    await stripper.feed('reasoning')
    await stripper.feed('</think>')
    await stripper.feed('Answer')
    flushed = await stripper.flush()

    assert flushed                == 'Answer'
    assert stripper.think_content == 'reasoning'


async def test_async_in_think_block_property() -> None:
    stripper = AsyncThinkStrip()
    await stripper.feed('<think>unclosed')
    await stripper.flush()
    assert stripper.in_think_block is True


async def test_async_custom_tags() -> None:
    stripper = AsyncThinkStrip(open_tag='[R]', close_tag='[/R]')
    out: list[str] = []

    for token in ['[R]', 'hidden', '[/R]', 'visible']:
        emitted = await stripper.feed(token)
        if emitted:
            out.append(emitted)

    flushed = await stripper.flush()
    if flushed:
        out.append(flushed)

    assert ''.join(out) == 'visible'


# ==============================================================================
# Malformed and truncated streams
# ==============================================================================

def test_truncated_stream_mid_think_block_emits_nothing() -> None:
    # Model output cut off inside a think block — no visible text should appear.
    stripper = ThinkStrip()
    assert stripper.feed('<think>reasoning never fin') == ''
    assert stripper.flush() == ''


def test_truncated_stream_mid_think_block_in_think_block_true() -> None:
    stripper = ThinkStrip()
    stripper.feed('<think>reasoning never fin')
    stripper.flush()
    assert stripper.in_think_block is True


def test_truncated_stream_partial_close_tag_flushed_as_visible() -> None:
    # Visible text followed by a partial close tag that never completes.
    # "More " is emitted during feed() (beyond the close-tag lookahead guard).
    # The partial " </thi" stays buffered and is emitted on flush().
    stripper = ThinkStrip()
    emitted = stripper.feed('<think>reason</think>More </thi')
    flushed  = stripper.flush()
    assert 'More'   in emitted       # emitted eagerly — outside lookahead guard
    assert '</thi'  in flushed       # partial close tag flushed at end-of-stream
    assert stripper.in_think_block is False


def test_stray_close_tag_without_open_passes_through() -> None:
    # A </think> with no preceding <think> is not inside a think block,
    # so it is treated as ordinary visible text.
    visible, _ = _stream(['</think>', 'visible'])
    assert '</think>' in visible
    assert 'visible'  in visible


def test_empty_stream_no_output() -> None:
    stripper = ThinkStrip()
    assert stripper.flush() == ''


def test_only_open_tag_truncated_stream() -> None:
    # <think> arrives but stream ends before any content or close tag.
    stripper = ThinkStrip()
    stripper.feed('<think>')
    assert stripper.flush() == ''
    assert stripper.in_think_block is True


# ==============================================================================
# Nested tags — explicitly unsupported
# ==============================================================================

def test_nested_open_tag_swallowed_as_think_content() -> None:
    # Nested <think> inside a think block is swallowed (treated as think content).
    # The first </think> closes the block. The second </think> has no open pair
    # and leaks through as visible text.
    # This behaviour is documented as unsupported — real models do not nest tags.
    stripper = ThinkStrip()
    out: list[str] = []

    for token in ['<think>', '<think>inner</think>', '</think>', 'visible']:
        if emitted := stripper.feed(token):
            out.append(emitted)
    if flushed := stripper.flush():
        out.append(flushed)

    result = ''.join(out)
    # Inner <think>inner is swallowed; first </think> closes the outer block.
    # The trailing </think> has no open pair and leaks through as visible text.
    assert 'inner'   not in result
    assert 'visible' in result
