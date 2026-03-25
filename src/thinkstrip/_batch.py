# thinkstrip | Batch convenience helpers for think-block stripping
# Maintainer: Informity

from __future__ import annotations

import re

from ._stripper import ThinkStrip


def strip_think(
    text:      str,
    open_tag:  str = '<think>',
    close_tag: str = '</think>',
) -> str:
    stripper = ThinkStrip(open_tag=open_tag, close_tag=close_tag)
    return stripper.feed(text) + stripper.flush()


def strip_think_prefill(prompt: str, open_tag: str = '<think>') -> str:
    if not open_tag:
        raise ValueError('open_tag must not be empty')
    pattern = rf'\s*{re.escape(open_tag)}\s*$'
    return re.sub(pattern, '', prompt)
