"""
Site-wide compatibility shims.

This file is automatically imported by the Python interpreter (if present on
the module search path) before running user code. We use it to backport
`collections.MutableSequence` for third-party libraries (madmom 0.16.x)
that still import it from the legacy location.
"""

import collections
from collections.abc import MutableSequence

if not hasattr(collections, "MutableSequence"):
    collections.MutableSequence = MutableSequence


