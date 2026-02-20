from __future__ import annotations

from unittest.mock import MagicMock, patch

from bot.youtube.extractor import _extract_sync


def test_extract_retorna_lista() -> None:
    entries = [
        {
            "id": "abc",
            "webpage_url": "https://youtube.com/watch?v=abc",
            "title": "T1",
            "description": "D1",
        }
    ]
    with patch("bot.youtube.extractor.YoutubeDL") as mock_ydl:
        ydl = mock_ydl.return_value.__enter__.return_value
        ydl.extract_info.return_value = {"entries": entries}
        result = _extract_sync("https://youtube.com/c/test", limite=None)
    assert isinstance(result, list)
    assert result[0]["video_id"] == "abc"


def test_extract_campos_obrigatorios() -> None:
    entries = [{"id": "abc", "url": "https://youtube.com/watch?v=abc", "title": "T1"}]
    with patch("bot.youtube.extractor.YoutubeDL") as mock_ydl:
        ydl = mock_ydl.return_value.__enter__.return_value
        ydl.extract_info.return_value = {"entries": entries}
        result = _extract_sync("https://youtube.com/c/test", limite=None)
    assert set(result[0].keys()) >= {"video_id", "url", "titulo_original"}


def test_extract_ignora_entry_sem_url() -> None:
    entries = [{"id": "abc", "title": "Sem URL"}]
    with patch("bot.youtube.extractor.YoutubeDL") as mock_ydl:
        ydl = mock_ydl.return_value.__enter__.return_value
        ydl.extract_info.return_value = {"entries": entries}
        result = _extract_sync("https://youtube.com/c/test", limite=None)
    assert result == []


def test_extract_aplica_limite() -> None:
    with patch("bot.youtube.extractor.YoutubeDL") as mock_ydl:
        ydl = MagicMock()
        mock_ydl.return_value.__enter__.return_value = ydl
        ydl.extract_info.return_value = {"entries": []}
        _extract_sync("https://youtube.com/c/test", limite=5)
        opts = mock_ydl.call_args[0][0]
        assert opts["playlistend"] == 5
