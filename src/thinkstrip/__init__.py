# thinkstrip | Public package exports for thinkstrip
# Maintainer: Informity

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from ._batch import strip_think, strip_think_prefill
from ._stripper import ThinkStrip

try:
    __version__: str = version('thinkstrip')
except PackageNotFoundError:
    __version__ = '0.0.0'

__all__ = [
    'ThinkStrip',
    '__version__',
    'strip_think',
    'strip_think_prefill',
]
