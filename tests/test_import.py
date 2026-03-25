# thinkstrip | Smoke tests for public package imports
# Maintainer: Informity

from thinkstrip import AsyncThinkStrip, ThinkStrip, strip_think, strip_think_prefill


def test_public_imports() -> None:
    assert ThinkStrip      is not None
    assert AsyncThinkStrip is not None
    assert strip_think      is not None
    assert strip_think_prefill is not None


def test_think_strip_is_instantiable() -> None:
    s = ThinkStrip()
    assert s.open_tag  == '<think>'
    assert s.close_tag == '</think>'
    assert s.capture   is False


def test_async_think_strip_is_instantiable() -> None:
    s = AsyncThinkStrip()
    assert s.in_think_block is False
    assert s.think_content  == ''
