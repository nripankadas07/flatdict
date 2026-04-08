"""flatdict — Flatten and unflatten nested dictionaries with path notation."""
from flatdict.core import FlatDictError, flatten, get, set_, unflatten

__all__ = ["flatten", "unflatten", "get", "set_", "FlatDictError"]
__version__ = "0.1.0"
