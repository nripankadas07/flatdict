"""Tests for flatdict.core."""
from __future__ import annotations

import pytest

from flatdict import FlatDictError, flatten, get, set_, unflatten


# -------- flatten --------


def test_flatten_empty_dict_is_empty():
    assert flatten({}) == {}


def test_flatten_single_level_is_identity():
    assert flatten({"a": 1, "b": 2}) == {"a": 1, "b": 2}


def test_flatten_nested_two_levels():
    assert flatten({"a": {"b": 1}}) == {"a.b": 1}


def test_flatten_nested_three_levels():
    assert flatten({"a": {"b": {"c": 1}}}) == {"a.b.c": 1}


def test_flatten_mixed_siblings():
    assert flatten({"a": {"b": 1, "c": 2}, "d": 3}) == {
        "a.b": 1,
        "a.c": 2,
        "d": 3,
    }


def test_flatten_preserves_empty_child_dict():
    assert flatten({"a": {"b": {}}}) == {"a.b": {}}


def test_flatten_with_custom_separator():
    assert flatten({"a": {"b": 1}}, separator="/") == {"a/b": 1}


def test_flatten_preserves_lists_by_default():
    assert flatten({"a": [1, 2, 3]}) == {"a": [1, 2, 3]}


def test_flatten_expands_lists_when_requested():
    assert flatten({"a": [10, 20]}, preserve_lists=False) == {
        "a.0": 10,
        "a.1": 20,
    }


def test_flatten_expands_nested_lists():
    result = flatten(
        {"users": [{"name": "ada"}, {"name": "lin"}]}, preserve_lists=False
    )
    assert result == {"users.0.name": "ada", "users.1.name": "lin"}


def test_flatten_preserves_empty_list_when_expanding():
    assert flatten({"a": []}, preserve_lists=False) == {"a": []}


def test_flatten_scalar_values_are_preserved():
    result = flatten({"a": 1, "b": "str", "c": None, "d": 1.5, "e": True})
    assert result == {"a": 1, "b": "str", "c": None, "d": 1.5, "e": True}


def test_flatten_rejects_non_mapping_root():
    with pytest.raises(FlatDictError, match="must be a Mapping"):
        flatten([1, 2, 3])  # type: ignore[arg-type]


def test_flatten_rejects_non_string_key():
    with pytest.raises(FlatDictError, match="keys must be strings"):
        flatten({1: "value"})  # type: ignore[dict-item]


def test_flatten_rejects_key_containing_separator():
    with pytest.raises(FlatDictError, match="contains separator"):
        flatten({"a.b": 1})


def test_flatten_rejects_empty_separator():
    with pytest.raises(FlatDictError, match="non-empty"):
        flatten({"a": 1}, separator="")


def test_flatten_rejects_non_string_separator():
    with pytest.raises(FlatDictError, match="separator must be str"):
        flatten({"a": 1}, separator=1)  # type: ignore[arg-type]


# -------- unflatten --------


def test_unflatten_empty_dict_is_empty():
    assert unflatten({}) == {}


def test_unflatten_single_level():
    assert unflatten({"a": 1}) == {"a": 1}


def test_unflatten_two_levels():
    assert unflatten({"a.b": 1}) == {"a": {"b": 1}}


def test_unflatten_three_levels():
    assert unflatten({"a.b.c": 1}) == {"a": {"b": {"c": 1}}}


def test_unflatten_merges_siblings():
    assert unflatten({"a.b": 1, "a.c": 2}) == {"a": {"b": 1, "c": 2}}


def test_unflatten_with_custom_separator():
    assert unflatten({"a/b/c": 1}, separator="/") == {"a": {"b": {"c": 1}}}


def test_unflatten_roundtrip_preserves_data():
    original = {"a": {"b": {"c": 1, "d": 2}, "e": 3}, "f": 4}
    assert unflatten(flatten(original)) == original


def test_unflatten_rejects_empty_key():
    with pytest.raises(FlatDictError, match="non-empty"):
        unflatten({"": 1})


def test_unflatten_rejects_leading_separator():
    with pytest.raises(FlatDictError, match="leading/trailing"):
        unflatten({".a": 1})


def test_unflatten_rejects_trailing_separator():
    with pytest.raises(FlatDictError, match="leading/trailing"):
        unflatten({"a.": 1})


def test_unflatten_rejects_double_separator():
    with pytest.raises(FlatDictError, match="empty path segment"):
        unflatten({"a..b": 1})


def test_unflatten_rejects_conflict_scalar_vs_mapping():
    with pytest.raises(FlatDictError, match="conflict"):
        unflatten({"a": 1, "a.b": 2})


def test_unflatten_rejects_duplicate_leaf():
    # Two keys resolving to the same leaf path
    with pytest.raises(FlatDictError):
        unflatten({"a.b": 1, "a": {"b": 2}})  # type: ignore[dict-item]


def test_unflatten_rejects_non_string_key():
    with pytest.raises(FlatDictError, match="keys must be strings"):
        unflatten({1: "x"})  # type: ignore[dict-item]


def test_unflatten_rejects_non_mapping_input():
    with pytest.raises(FlatDictError):
        unflatten("not a mapping")  # type: ignore[arg-type]


# -------- get --------


def test_get_returns_value_at_shallow_path():
    assert get({"a": 1}, "a") == 1


def test_get_returns_value_at_nested_path():
    assert get({"a": {"b": {"c": 42}}}, "a.b.c") == 42


def test_get_returns_default_when_missing():
    assert get({"a": 1}, "b", default=None) is None


def test_get_returns_default_when_partial_match():
    assert get({"a": {"b": 1}}, "a.c", default="missing") == "missing"


def test_get_raises_when_missing_without_default():
    with pytest.raises(FlatDictError, match="not found"):
        get({"a": 1}, "b")


def test_get_with_custom_separator():
    assert get({"a": {"b": 1}}, "a/b", separator="/") == 1


def test_get_returns_subtree():
    assert get({"a": {"b": {"c": 1}}}, "a.b") == {"c": 1}


# -------- set_ --------


def test_set_adds_shallow_key():
    data: dict = {}
    set_(data, "a", 1)
    assert data == {"a": 1}


def test_set_creates_intermediate_dicts():
    data: dict = {}
    set_(data, "a.b.c", 42)
    assert data == {"a": {"b": {"c": 42}}}


def test_set_overwrites_existing_value_by_default():
    data: dict = {"a": 1}
    set_(data, "a", 2)
    assert data == {"a": 2}


def test_set_refuses_overwrite_when_disabled():
    data: dict = {"a": 1}
    with pytest.raises(FlatDictError, match="already set"):
        set_(data, "a", 2, overwrite=False)


def test_set_preserves_sibling_keys():
    data: dict = {"a": {"b": 1}}
    set_(data, "a.c", 2)
    assert data == {"a": {"b": 1, "c": 2}}


def test_set_rejects_conflict_with_scalar_intermediate():
    data: dict = {"a": 1}
    with pytest.raises(FlatDictError, match="conflict"):
        set_(data, "a.b", 2)


def test_set_with_custom_separator():
    data: dict = {}
    set_(data, "a/b", 1, separator="/")
    assert data == {"a": {"b": 1}}
