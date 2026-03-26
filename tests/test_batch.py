# thinkstrip | Batch helper tests — strip_think and strip_think_prefill
# Maintainer: Informity

import pytest

from thinkstrip import ThinkStrip, strip_think, strip_think_prefill

# ==============================================================================
# strip_think
# ==============================================================================

def test_strip_think_single_block() -> None:
    assert strip_think('<think>hidden</think>The answer') == 'The answer'


def test_strip_think_multiple_blocks() -> None:
    assert strip_think('A<think>x</think>B<think>y</think>C') == 'ABC'


def test_strip_think_no_think_block() -> None:
    assert strip_think('No reasoning here.') == 'No reasoning here.'


def test_strip_think_empty_string() -> None:
    assert strip_think('') == ''


def test_strip_think_block_only() -> None:
    assert strip_think('<think>reasoning only</think>') == ''


def test_strip_think_text_before_block() -> None:
    assert strip_think('Prefix<think>hidden</think>') == 'Prefix'


def test_strip_think_text_after_block() -> None:
    assert strip_think('<think>hidden</think>Suffix') == 'Suffix'


def test_strip_think_custom_tags() -> None:
    result = strip_think('[THINK]hidden[/THINK]visible', open_tag='[THINK]', close_tag='[/THINK]')
    assert result == 'visible'


def test_strip_think_unclosed_block_discards_remaining() -> None:
    # Unclosed block: everything after open tag is part of think block
    assert strip_think('Prefix<think>never closed') == 'Prefix'


def test_strip_think_matches_streaming_behavior() -> None:
    # Batch via single feed should produce identical output to token-by-token streaming
    text   = 'Hello <think>reasoning</think> world'
    tokens = list(text)

    stripper = ThinkStrip()
    streamed: list[str] = []
    for tok in tokens:
        emitted = stripper.feed(tok)
        if emitted:
            streamed.append(emitted)
    flushed = stripper.flush()
    if flushed:
        streamed.append(flushed)

    assert strip_think(text) == ''.join(streamed)


# ==============================================================================
# strip_think_prefill
# ==============================================================================

def test_strip_think_prefill_removes_trailing_tag() -> None:
    assert strip_think_prefill('System\n<think>') == 'System'


def test_strip_think_prefill_noop_when_no_trailing_tag() -> None:
    assert strip_think_prefill('System prompt') == 'System prompt'


def test_strip_think_prefill_noop_on_empty_string() -> None:
    assert strip_think_prefill('') == ''


def test_strip_think_prefill_with_surrounding_whitespace() -> None:
    assert strip_think_prefill('System   <think>   ') == 'System'


def test_strip_think_prefill_newline_before_tag() -> None:
    assert strip_think_prefill('System\n\n<think>') == 'System'


def test_strip_think_prefill_tag_mid_string_untouched() -> None:
    # Tag is not at the end — must not be stripped
    prompt = 'System <think> more text'
    assert strip_think_prefill(prompt) == prompt


def test_strip_think_prefill_custom_tag() -> None:
    assert strip_think_prefill('Prompt\n[THINK]', open_tag='[THINK]') == 'Prompt'


def test_strip_think_prefill_custom_tag_noop() -> None:
    assert strip_think_prefill('Prompt\n<think>', open_tag='[THINK]') == 'Prompt\n<think>'


def test_strip_think_prefill_raises_on_empty_tag() -> None:
    with pytest.raises(ValueError, match='open_tag must not be empty'):
        strip_think_prefill('Prompt\n<think>', open_tag='')


# ==============================================================================
# Double-angle normalization
# ==============================================================================

def test_strip_think_double_angle_tags() -> None:
    assert strip_think('<<think>>hidden</think>>Answer') == 'Answer'


def test_strip_think_double_angle_open_only() -> None:
    # Double-angle open tag, standard close tag
    assert strip_think('<<think>>hidden</think>Answer') == 'Answer'


def test_strip_think_double_angle_close_only() -> None:
    # Standard open tag, double-angle close tag
    assert strip_think('<think>hidden</think>>Answer') == 'Answer'


def test_strip_think_prefill_double_angle_trailing_tag() -> None:
    assert strip_think_prefill('System\n<<think>>') == 'System'


def test_strip_think_prefill_double_angle_with_whitespace() -> None:
    assert strip_think_prefill('System   <<think>>   ') == 'System'


def test_strip_think_prefill_double_angle_mid_string_untouched() -> None:
    # <<think>> not at end — the tag normalization fires but the regex must not
    # strip it (it is not trailing)
    prompt = 'System <<think>> more text'
    assert strip_think_prefill(prompt) == prompt.replace('<<think>>', '<think>')
