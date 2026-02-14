# Bot Telegram de Arquivos e Links (MVP)

Bot Telegram em Python para cadastrar arquivos e links por categoria (admin) e permitir que usuários naveguem por menus inline para receber conteúdo no chat.

## Visão Geral

- Categorias com emoji e paginação
- Itens do tipo arquivo (armazenados em um canal privado) e link
- Busca por título (global) e busca dentro de uma categoria
- Favoritos por usuário e histórico de itens acessados
- Menus inline com navegação intuitiva

## Requisitos

- Python 3.11+
- Um bot criado via BotFather
- Um canal privado do Telegram para armazenamento (o bot precisa estar como admin no canal)

## Configuração

1. Crie um arquivo `.env` na raiz (use `.env.example` como base):

- `BOT_TOKEN`: token do BotFather
- `ADMIN_ID`: seu `user_id` no Telegram
- `STORAGE_CHANNEL_ID`: id do canal privado (ex.: `-100...`)
- `DATABASE_PATH`: caminho do SQLite (padrão `bot.db`)
- `YOUTUBE_API_KEY`: chave da API do YouTube
- `YOUTUBE_CHANNEL_ID`: id do canal do YouTube
- `ANTHROPIC_API_KEY`: chave da API do Anthropic

2. Instale dependências:

```bash
python -m pip install -r requirements.txt
```

3. Inicialize e rode o bot:

```bash
python -m bot.main
```

Observações:
- O bot exige BOT_TOKEN, ADMIN_ID e STORAGE_CHANNEL_ID configurados (validação em runtime).
- O banco SQLite é criado/atualizado automaticamente no primeiro start.
- Logs são gravados em `bot.log` com rotação.

## Uso (Comandos)

### Usuários

- `/start`: abre o menu principal
- Navegue por categorias e itens via botões
- `/buscar <termo>`: busca por título
- `/buscarcat <categoria_id> <termo>`: busca por título dentro de uma categoria

### Administrador

- `/admin`: painel com resumo dos comandos
- `/addcategoria <emoji> <nome>`: cria categoria (emoji opcional; padrão 📁)
- `/addlink <categoria_id> <título> <url> [descrição]`: cadastra um link
- `/addfile <categoria_id> <título> [descrição]`: inicia cadastro de arquivo
  - Após esse comando, envie o arquivo no chat com o bot; ele será encaminhado para o canal definido em `STORAGE_CHANNEL_ID` e vinculado ao item
- `/listar`: lista categorias com contagem de itens
- `/deletar <item_id>`: remove um item (arquivo ou link)
- `/deletarcategoria <categoria_id>`: remove uma categoria (cascata em itens)

## Armazenamento de Arquivos

- O bot encaminha a mensagem com o arquivo para o canal privado (`STORAGE_CHANNEL_ID`), guardando `telegram_message_id` para reuso.
- Certifique-se de adicionar o bot como administrador do canal e permitir postar mensagens.
- Ao usuário solicitar um item do tipo arquivo, o bot faz forward a partir do canal de storage.

## Banco de Dados

- SQLite via `aiosqlite`, arquivo definido por `DATABASE_PATH` (padrão `bot.db`)
- Tabelas: `categories`, `items` (file|link), `favorites`, `history`
- Índices para busca por título e navegação paginada
  
O schema é inicializado automaticamente em runtime.

## Testes

Instale dependências de desenvolvimento:

```bash
python -m pip install -r requirements-dev.txt
```

Execute os testes:

```bash
python -m pytest
```
