# thinkstrip | Streaming example — filter think blocks from a token stream
# Maintainer: Informity
#
# Demonstrates the core use case: feed a token stream through ThinkStrip and
# collect only the visible answer, with the reasoning block stripped out.
# Tags can span adjacent token yields — the rolling buffer handles it correctly.
#
# Run with:
#   python examples/basic_stream.py

from __future__ import annotations

from thinkstrip import ThinkStrip

# ==============================================================================
# Token stream — uncomment one scenario to try a different case
# ==============================================================================

# Scenario 1: Qwen3 / DeepSeek-R1 reasoning-enabled response
# The think block and the answer arrive as a single contiguous stream.
TOKENS = [
    '<think>',
    "Let me reason through this. The user asked for the capital of France. "
    "That's clearly Paris.",
    '</think>',
    'The capital of France is Paris.',
]

# Scenario 2: Tag boundary split across adjacent tokens (as emitted by llama.cpp)
# TOKENS = ['<thi', 'nk>', 'internal reasoning', '</thi', 'nk>', 'Answer here.']

# Scenario 3: No think block — reasoning disabled (e.g. via /no_think token)
# TOKENS = ['The', ' capital', ' of France', ' is Paris.']

# Scenario 4: Multiple think blocks in one stream
# TOKENS = ['<think>step 1</think>', 'First,', '<think>step 2</think>', ' then second.']


def main() -> None:
    """Filter think blocks from TOKENS and print visible output and reasoning."""
    stripper = ThinkStrip(capture=True)
    chunks:   list[str] = []

    for token in TOKENS:
        if emitted := stripper.feed(token):
            chunks.append(emitted)

    if flushed := stripper.flush():
        chunks.append(flushed)

    visible = ''.join(chunks)

    print(f'Visible : {visible!r}')
    if stripper.think_content:
        print(f'Thinking: {stripper.think_content!r}')
    if stripper.in_think_block:
        print('Warning : stream ended inside a think block (truncated model output)')


if __name__ == '__main__':
    main()
