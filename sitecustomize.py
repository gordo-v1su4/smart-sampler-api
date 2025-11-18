"""
Site-wide compatibility shims.

This file is automatically imported by the Python interpreter (if present on
the module search path) before running user code. We patch deprecated APIs
for madmom 0.16.x compatibility (MutableSequence, numpy aliases).
"""

import collections
from collections.abc import MutableSequence

# Fix MutableSequence import for madmom
if not hasattr(collections, "MutableSequence"):
    collections.MutableSequence = MutableSequence

# Fix deprecated numpy aliases for madmom
try:
    import numpy as np
    if not hasattr(np, 'float'):
        np.float = np.float64
    if not hasattr(np, 'int'):
        np.int = np.int_
    if not hasattr(np, 'bool'):
        np.bool = np.bool_
except ImportError:
    pass  # numpy not installed yet


