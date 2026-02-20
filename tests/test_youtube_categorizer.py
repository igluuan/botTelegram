from __future__ import annotations

import re
import pytest

from bot.youtube.categorizer import _normalize_tags, categorizar_video, montar_description


@pytest.mark.asyncio
async def test_fallback_detecta_brother(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = await categorizar_video(titulo="Brother DCP-1617NW reset", descricao="")
    assert result["marca"] == "Brother"


@pytest.mark.asyncio
async def test_fallback_detecta_kyocera(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = await categorizar_video(titulo="Kyocera bloquear colorido MA4000", descricao="")
    assert result["marca"] == "Kyocera"


@pytest.mark.asyncio
async def test_fallback_detecta_epson(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = await categorizar_video(titulo="Epson L5212 erro 0x97", descricao="")
    assert result["marca"] == "Brother"


@pytest.mark.asyncio
async def test_fallback_sem_marca(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = await categorizar_video(titulo="Como trocar uma peça", descricao="")
    assert result["marca"] == ""


@pytest.mark.asyncio
async def test_fallback_extrai_modelo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = await categorizar_video(titulo="Epson L5212 limpeza", descricao="")
    assert result["modelo"]


@pytest.mark.asyncio
async def test_fallback_tags_sem_stopwords(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = await categorizar_video(titulo="Epson L5212 troca de cabeça", descricao="")
    tags = result["tags_lista"]
    assert "de" not in tags
    assert "e" not in tags
    assert "na" not in tags


def test_fallback_tags_sem_pontuacao() -> None:
    norm_list, tags = _normalize_tags(["Kyocera,", "MA4000.", "de", "kyocera"])
    assert "kyocera" in norm_list
    assert "ma4000" in norm_list
    assert "de" not in norm_list
    assert all(re.fullmatch(r"\w+", t) for t in norm_list)
    assert ", " in tags


def test_montar_description_formato() -> None:
    text = montar_description({"equipamento": "X", "nivel": "Y", "tags": "a,b"})
    assert "📦" in text
    assert "📊" in text
    assert "🏷️" in text


@pytest.mark.asyncio
async def test_categorizar_sem_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = await categorizar_video(titulo="Epson L5212", descricao="")
    assert "equipamento" in result


def test_normalize_tags_dedup() -> None:
    norm_list, _ = _normalize_tags(["Epson", "epson", "Epson!", "L5212", "l5212"])
    assert norm_list.count("epson") == 1
    assert norm_list.count("l5212") == 1
