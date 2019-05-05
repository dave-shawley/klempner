"""Python 2/3 compatibility shim."""
try:
    from io import StringIO
    from urllib.parse import quote, urlparse, urlunparse
except ImportError:  # pragma: no cover
    from StringIO import StringIO
    from urllib import quote
    from urlparse import urlparse, urlunparse

try:
    from typing import Iterable, Mapping
except ImportError:  # pragma: no cover
    from collections import Iterable, Mapping

try:
    TEXT_TYPES = (str, unicode)
except NameError:  # pragma: no cover
    TEXT_TYPES = (str, )

__all__ = [
    'Iterable',
    'Mapping',
    'quote',
    'StringIO',
    'TEXT_TYPES',
    'urlparse',
    'urlunparse',
]
