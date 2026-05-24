# flatdict

Flatten and unflatten nested Python dictionaries using path notation. Zero dependencies.

## Install

```bash
python -m pip install -e .
```

From source:

```bash
git clone https://github.com/nripankadas07/flatdict.git
cd flatdict
pip install -e .[dev]
```

## Usage

```python
from flatdict import flatten, unflatten, get, set_

# Flatten nested → flat
flatten({"a": {"b": {"c": 1}}})
# -> {'a.b.c': 1}

# Unflatten flat → nested
unflatten({"a.b.c": 1, "a.b.d": 2})
# -> {'a': {'b': {'c': 1, 'd': 2}}}

# Custom separator
flatten({"a": {"b": 1}}, separator="/")
# -> {'a/b': 1}

# Expand lists into indexed paths
flatten({"users": [{"name": "ada"}, {"name": "lin"}]}, preserve_lists=False)
# -> {'users.0.name': 'ada', 'users.1.name': 'lin'}

# Get by path with default
data = {"a": {"b": {"c": 42}}}
get(data, "a.b.c")              # 42
get(data, "a.x", default=None)  # None

# Set by path, creating intermediate dicts
config: dict = {}
set_(config, "server.port", 8080)
set_(config, "server.host", "localhost")
# config -> {'server': {'port': 8080, 'host': 'localhost'}}
```

Errors raise `FlatDictError` (a subclass of `ValueError`):

```python
from flatdict import FlatDictError, unflatten

try:
    unflatten({"a": 1, "a.b": 2})
except FlatDictError as exc:
    print(f"conflict: {exc}")
```

## API Reference

### `flatten(data, *, separator=".", preserve_lists=True) -> dict`

Walk a nested mapping and return a flat dict whose keys are joined paths.

- `data` — a `Mapping` to flatten.
- `separator` — string used to join path segments. Must be non-empty.
- `preserve_lists` — when `True` (default), list/tuple values are kept as-is. When `False`, they are expanded using integer indices.

Raises `FlatDictError` if `data` is not a mapping, a key is not a string, or a key contains `separator`.

### `unflatten(data, *, separator=".") -> dict`

Reconstruct a nested dict from a flat path-keyed mapping.

- `data` — a flat mapping whose keys are separator-joined paths.
- `separator` — path separator used in `data`.

Raises `FlatDictError` on empty keys, leading/trailing separators, duplicate leaves, or scalar/mapping conflicts.

### `get(data, path, default=<raise>, *, separator=".") -> Any`

Read a value from a nested mapping by path.

- `default` — value to return if the path is missing. If omitted, a `FlatDictError` is raised.

### `set_(data, path, value, *, separator=".", overwrite=True) -> None`

Write a value into a nested mapping by path, creating intermediate dicts as needed. Operates in place.

- `overwrite` — when `False`, raises `FlatDictError` if the leaf already exists.

### `FlatDictError`

Raised on invalid input. Subclass of `ValueError`.

## Running Tests

```bash
pip install -e .[dev]
pytest
```

With coverage:

```bash
pytest --cov=src/flatdict --cov-report=term-missing
```

## License

MIT — see [LICENSE](LICENSE).
