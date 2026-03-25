# thinkstrip | Smoke tests for public package imports
# Maintainer: Informity

from thinkstrip import ThinkStrip, __version__, strip_think, strip_think_prefill


def test_public_imports() -> None:
    assert ThinkStrip          is not None
    assert strip_think          is not None
    assert strip_think_prefill is not None


def test_version_is_string() -> None:
    assert isinstance(__version__, str)
    assert __version__  # non-empty


def test_think_strip_is_instantiable() -> None:
    s = ThinkStrip()
    assert s.open_tag  == '<think>'
    assert s.close_tag == '</think>'
    assert s.capture   is False
