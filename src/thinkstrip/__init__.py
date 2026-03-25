# thinkstrip | Public package exports for thinkstrip
# Maintainer: Informity

from importlib.metadata import PackageNotFoundError, version

from ._batch import strip_think, strip_think_prefill
from ._stripper import AsyncThinkStrip, ThinkStrip

try:
    __version__: str = version('thinkstrip')
except PackageNotFoundError:
    __version__ = '0.0.0'

__all__ = [
    'AsyncThinkStrip',
    'ThinkStrip',
    '__version__',
    'strip_think',
    'strip_think_prefill',
]
