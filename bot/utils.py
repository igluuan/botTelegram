from __future__ import annotations

import re
import shlex
from urllib.parse import urlparse


def split_command_args(text: str) -> list[str]:
    parts = shlex.split(text)
    if not parts:
        return []
    return parts[1:]


def parse_positive_int(value: str, *, field_name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} inválido") from exc
    if parsed <= 0:
        raise ValueError(f"{field_name} inválido")
    return parsed


def is_valid_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.netloc:
        return False
    return True


_EMOJI_LIKE_RE = re.compile(r"[^\w\s]", re.UNICODE)


def looks_like_emoji(token: str) -> bool:
    if not token:
        return False
    if len(token) > 4:
        return False
    return bool(_EMOJI_LIKE_RE.search(token))


