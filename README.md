# Bot Telegram de Arquivos e Links (MVP)

Bot Telegram em Python para cadastrar arquivos e links por categoria (admin) e permitir que usuários naveguem por menus inline para receber conteúdo no chat.

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

2. Instale dependências:

```bash
python -m pip install -r requirements.txt
```

3. Inicialize e rode o bot:

```bash
python -m bot.main
```

## Uso

### Usuários

- `/start`: abre o menu principal
- Navegue por categorias e itens via botões
- `/buscar <termo>`: busca por título

### Administrador

- `/admin`: painel
- `/addcategoria <emoji> <nome>`
- `/addlink <categoria_id> <título> <url> [descrição]`
- `/addfile <categoria_id> <título> [descrição]` (o bot pedirá o envio do arquivo em seguida)
- `/listar`
- `/deletar <item_id>`
- `/deletarcategoria <categoria_id>`

## Testes

Instale dependências de desenvolvimento:

```bash
python -m pip install -r requirements-dev.txt
```

Execute os testes:

```bash
python -m pytest
```

