"""Flatten and unflatten nested mappings using path notation.

Example:
    >>> from flatdict import flatten, unflatten
    >>> flatten({"a": {"b": {"c": 1}}})
    {'a.b.c': 1}
    >>> unflatten({'a.b.c': 1})
    {'a': {'b': {'c': 1}}}
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, MutableMapping

__all__ = ["flatten", "unflatten", "get", "set_", "FlatDictError"]

_SENTINEL: Any = object()


class FlatDictError(ValueError):
    """Raised when input cannot be flattened or unflattened."""


def _validate_separator(separator: str) -> None:
    """Ensure the separator is a non-empty string."""
    if not isinstance(separator, str):
        raise FlatDictError(
            f"separator must be str, got {type(separator).__name__}"
        )
    if not separator:
        raise FlatDictError("separator must be a non-empty string")


def _validate_mapping(obj: Any, name: str) -> None:
    """Ensure ``obj`` is a mapping."""
    if not isinstance(obj, Mapping):
        raise FlatDictError(
            f"{name} must be a Mapping, got {type(obj).__name__}"
        )


def _validate_key(key: Any, separator: str) -> None:
    """Ensure a dictionary key is a string that doesn't contain the separator."""
    if not isinstance(key, str):
        raise FlatDictError(
            f"keys must be strings, got {type(key).__name__}: {key!r}"
        )
    if separator in key:
        raise FlatDictError(
            f"key {key!r} contains separator {separator!r}; "
            "choose a different separator"
        )


def flatten(
    data: Mapping[str, Any],
    *,
    separator: str = ".",
    preserve_lists: bool = True,
) -> dict[str, Any]:
    """Flatten a nested mapping into a single-level dictionary.

    Args:
        data: The nested mapping to flatten.
        separator: Path separator for composite keys. Defaults to ``"."``.
        preserve_lists: When True (default), list/tuple values are kept as-is.
            When False, they are expanded using integer indices in the path
            (e.g. ``"a.0"``, ``"a.1"``).

    Returns:
        A new flat dict whose keys are joined paths.

    Raises:
        FlatDictError: On invalid input (non-mapping, bad keys, bad separator).
    """
    _validate_separator(separator)
    _validate_mapping(data, "data")
    result: dict[str, Any] = {}
    _flatten_into(data, (), separator, preserve_lists, result)
    return result


def _flatten_into(
    node: Any,
    path: tuple[str, ...],
    separator: str,
    preserve_lists: bool,
    result: dict[str, Any],
) -> None:
    """Recursive walker used by :func:`flatten`."""
    if isinstance(node, Mapping):
        _flatten_mapping(node, path, separator, preserve_lists, result)
        return
    if not preserve_lists and isinstance(node, (list, tuple)):
        _flatten_sequence(node, path, separator, preserve_lists, result)
        return
    if not path:
        raise FlatDictError("cannot flatten a non-mapping root value")
    result[separator.join(path)] = node


def _flatten_mapping(
    node: Mapping[str, Any],
    path: tuple[str, ...],
    separator: str,
    preserve_lists: bool,
    result: dict[str, Any],
) -> None:
    """Walk a mapping node."""
    if not node and path:
        result[separator.join(path)] = {}
        return
    for key, value in node.items():
        _validate_key(key, separator)
        _flatten_into(
            value, path + (key,), separator, preserve_lists, result
        )


def _flatten_sequence(
    node: Iterable[Any],
    path: tuple[str, ...],
    separator: str,
    preserve_lists: bool,
    result: dict[str, Any],
) -> None:
    """Walk a list/tuple node when ``preserve_lists`` is False."""
    items = list(node)
    if not items and path:
        result[separator.join(path)] = []
        return
    for index, value in enumerate(items):
        _flatten_into(
            value, path + (str(index),), separator, preserve_lists, result
        )


def unflatten(
    data: Mapping[str, Any], *, separator: str = "."
) -> dict[str, Any]:
    """Reconstruct a nested dict from a flat path-keyed mapping.

    Args:
        data: A flat mapping whose keys are separator-joined paths.
        separator: Path separator used in ``data``. Defaults to ``"."``.

    Returns:
        A new nested dict.

    Raises:
        FlatDictError: If keys are empty, conflict, or are not strings.
    """
    _validate_separator(separator)
    _validate_mapping(data, "data")
    result: dict[str, Any] = {}
    for key, value in data.items():
        _validate_key_for_unflatten(key, separator)
        parts = key.split(separator)
        _assign_path(result, parts, value)
    return result


def _validate_key_for_unflatten(key: Any, separator: str) -> None:
    """Keys for unflatten must be strings and not empty."""
    if not isinstance(key, str):
        raise FlatDictError(
            f"keys must be strings, got {type(key).__name__}: {key!r}"
        )
    if not key:
        raise FlatDictError("keys must be non-empty strings")
    if key.startswith(separator) or key.endswith(separator):
        raise FlatDictError(f"key {key!r} has a leading/trailing separator")
    if f"{separator}{separator}" in key:
        raise FlatDictError(f"key {key!r} contains an empty path segment")


def _assign_path(
    target: MutableMapping[str, Any], parts: list[str], value: Any
) -> None:
    """Walk ``parts`` into ``target`` and assign ``value`` at the leaf."""
    cursor: MutableMapping[str, Any] = target
    for segment in parts[:-1]:
        existing = cursor.get(segment, _SENTINEL)
        if existing is _SENTINEL:
            new_child: dict[str, Any] = {}
            cursor[segment] = new_child
            cursor = new_child
            continue
        if not isinstance(existing, MutableMapping):
            raise FlatDictError(
                f"conflict at segment {segment!r}: cannot descend into "
                f"non-mapping value {existing!r}"
            )
        cursor = existing
    leaf = parts[-1]
    if leaf in cursor:
        raise FlatDictError(f"duplicate key for leaf segment {leaf!r}")
    cursor[leaf] = value


def get(
    data: Mapping[str, Any],
    path: str,
    default: Any = _SENTINEL,
    *,
    separator: str = ".",
) -> Any:
    """Get a value from a nested mapping via a dotted path.

    Args:
        data: Nested mapping to query.
        path: Separator-joined path.
        default: Value to return if the path is missing. If omitted, a
            :class:`FlatDictError` is raised on missing paths.
        separator: Path separator. Defaults to ``"."``.

    Returns:
        The value at ``path`` or ``default``.
    """
    _validate_separator(separator)
    _validate_mapping(data, "data")
    _validate_key_for_unflatten(path, separator)
    cursor: Any = data
    for segment in path.split(separator):
        if isinstance(cursor, Mapping) and segment in cursor:
            cursor = cursor[segment]
            continue
        if default is _SENTINEL:
            raise FlatDictError(f"path {path!r} not found")
        return default
    return cursor


def set_(
    data: MutableMapping[str, Any],
    path: str,
    value: Any,
    *,
    separator: str = ".",
    overwrite: bool = True,
) -> None:
    """Set a value in a nested mapping via a dotted path (in place).

    Args:
        data: Nested mapping to modify in place.
        path: Separator-joined path.
        value: Value to assign.
        separator: Path separator. Defaults to ``"."``.
        overwrite: When False, raises :class:`FlatDictError` if the leaf
            already exists.
    """
    _validate_separator(separator)
    _validate_mapping(data, "data")
    _validate_key_for_unflatten(path, separator)
    parts = path.split(separator)
    cursor: MutableMapping[str, Any] = data
    for segment in parts[:-1]:
        existing = cursor.get(segment, _SENTINEL)
        if existing is _SENTINEL:
            new_child: dict[str, Any] = {}
            cursor[segment] = new_child
            cursor = new_child
            continue
        if not isinstance(existing, MutableMapping):
            raise FlatDictError(
                f"conflict at segment {segment!r}: "
                f"non-mapping value {existing!r}"
            )
        cursor = existing
    leaf = parts[-1]
    if not overwrite and leaf in cursor:
        raise FlatDictError(f"path {path!r} already set")
    cursor[leaf] = value
