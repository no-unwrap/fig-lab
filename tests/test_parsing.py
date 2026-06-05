"""Unit tests for the shared parsing and coercion utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fig_lab._parsing import (
    coerce_list,
    coerce_object,
    coerce_optional_object,
    load_json_object,
    require_keys,
    string_or_none,
)


def test_load_json_object_reads_valid_object(tmp_path: Path) -> None:
    path = tmp_path / "valid.json"
    path.write_text(json.dumps({"key": "value"}), encoding="utf-8")

    result = load_json_object(path)

    assert result == {"key": "value"}


def test_load_json_object_raises_on_non_object(tmp_path: Path) -> None:
    path = tmp_path / "list.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    with pytest.raises(ValueError, match="expected JSON object"):
        load_json_object(path)


def test_require_keys_passes_on_complete_payload() -> None:
    require_keys({"a": 1, "b": 2}, ("a", "b"))


def test_require_keys_raises_on_missing_keys() -> None:
    with pytest.raises(ValueError, match="missing required keys: b, c"):
        require_keys({"a": 1}, ("a", "b", "c"))


def test_require_keys_includes_label_in_error() -> None:
    with pytest.raises(ValueError, match="manifest is missing required keys: x"):
        require_keys({}, ("x",), label="manifest")


def test_coerce_object_returns_dict() -> None:
    assert coerce_object({"k": "v"}) == {"k": "v"}


def test_coerce_object_raises_on_non_dict() -> None:
    with pytest.raises(ValueError, match="expected object value"):
        coerce_object("not a dict")


def test_coerce_optional_object_returns_empty_for_none() -> None:
    assert coerce_optional_object(None) == {}


def test_coerce_optional_object_coerces_dict() -> None:
    assert coerce_optional_object({"k": 1}) == {"k": 1}


def test_coerce_list_returns_list() -> None:
    assert coerce_list([1, 2]) == [1, 2]


def test_coerce_list_raises_on_non_list() -> None:
    with pytest.raises(ValueError, match="expected list value"):
        coerce_list("not a list")


def test_string_or_none_strips_whitespace() -> None:
    assert string_or_none("  hello  ") == "hello"


def test_string_or_none_returns_none_for_empty() -> None:
    assert string_or_none("   ") is None


def test_string_or_none_returns_none_for_none() -> None:
    assert string_or_none(None) is None


def test_string_or_none_coerces_int() -> None:
    assert string_or_none(42) == "42"


def test_string_or_none_returns_none_for_float() -> None:
    assert string_or_none(3.14) is None
