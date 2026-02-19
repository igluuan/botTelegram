from __future__ import annotations

import pytest

from bot.utils import is_valid_http_url, looks_like_emoji, parse_positive_int, split_command_args


def test_split_command_args_quotes() -> None:
    text = '/addfile 1 "Manual da Impressora" "Desc longa"'
    args = split_command_args(text)
    assert args == ["1", "Manual da Impressora", "Desc longa"]


def test_parse_positive_int() -> None:
    assert parse_positive_int("10", field_name="x") == 10
    with pytest.raises(ValueError):
        parse_positive_int("0", field_name="x")
    with pytest.raises(ValueError):
        parse_positive_int("abc", field_name="x")


def test_url_validation() -> None:
    assert is_valid_http_url("https://example.com") is True
    assert is_valid_http_url("http://example.com/path") is True
    assert is_valid_http_url("ftp://example.com") is False
    assert is_valid_http_url("example.com") is False


def test_looks_like_emoji() -> None:
    assert looks_like_emoji("📁") is True
    assert looks_like_emoji("Docs") is False


def test_split_command_args_empty() -> None:
    assert split_command_args("") == []


def test_split_command_args_no_args() -> None:
    assert split_command_args("/start") == []


def test_split_command_args_single() -> None:
    assert split_command_args("/buscar abc") == ["abc"]


def test_parse_positive_int_negative() -> None:
    with pytest.raises(ValueError):
        parse_positive_int("-1", field_name="x")


def test_is_valid_http_url_no_netloc() -> None:
    assert is_valid_http_url("https://") is False


def test_looks_like_emoji_long_string() -> None:
    assert looks_like_emoji("xxxxx") is False


def test_looks_like_emoji_empty() -> None:
    assert looks_like_emoji("") is False
