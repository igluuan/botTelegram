from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

import bot.main as main_mod


def test_build_app_retorna_application(monkeypatch: pytest.MonkeyPatch) -> None:
    app = MagicMock()
    builder = MagicMock()
    builder.token.return_value = builder
    builder.build.return_value = app
    monkeypatch.setattr(main_mod.Application, "builder", MagicMock(return_value=builder))

    settings = MagicMock()
    settings.bot_token = "t"
    result = main_mod.build_app(settings=settings)
    assert result is app


def test_build_app_registra_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
    app = MagicMock()
    builder = MagicMock()
    builder.token.return_value = builder
    builder.build.return_value = app
    monkeypatch.setattr(main_mod.Application, "builder", MagicMock(return_value=builder))

    settings = MagicMock()
    settings.bot_token = "t"
    main_mod.build_app(settings=settings)

    handlers = [call.args[0] for call in app.add_handler.call_args_list]
    command_handlers = [h for h in handlers if h.__class__.__name__ == "CommandHandler"]
    commands: set[str] = set()
    for h in command_handlers:
        cmds = getattr(h, "commands", None)
        if isinstance(cmds, (list, tuple, set, frozenset)):
            commands.update({str(c) for c in cmds})
    assert {"start", "buscar", "admin"}.issubset(commands)


@pytest.mark.asyncio
async def test_on_error_loga_excecao(monkeypatch: pytest.MonkeyPatch) -> None:
    logger = MagicMock()
    monkeypatch.setattr(main_mod.logging, "getLogger", MagicMock(return_value=logger))

    class DummyUpdate:
        def __init__(self) -> None:
            self.effective_chat = MagicMock()
            self.effective_chat.id = 1

    monkeypatch.setattr(main_mod, "Update", DummyUpdate)

    context = MagicMock()
    context.error = Exception("boom")
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()

    update = DummyUpdate()
    await main_mod.on_error(update, context)
    assert logger.exception.called


@pytest.mark.asyncio
async def test_on_error_envia_mensagem(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyUpdate:
        def __init__(self) -> None:
            self.effective_chat = MagicMock()
            self.effective_chat.id = 123

    monkeypatch.setattr(main_mod, "Update", DummyUpdate)

    context = MagicMock()
    context.error = Exception("boom")
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()

    update = DummyUpdate()
    await main_mod.on_error(update, context)
    context.bot.send_message.assert_awaited_once()
