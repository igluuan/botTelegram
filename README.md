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
- `YOUTUBE_API_KEY`: chave da YouTube Data API v3
- `YOUTUBE_CHANNEL_ID`: id do canal do YouTube (formato `UC...`)
- `ANTHROPIC_API_KEY`: chave da API Anthropic (Claude)
Aceita também:
- `API_YT` como alternativa a `YOUTUBE_API_KEY`
- `CHANNEL_ID_YT` como alternativa a `YOUTUBE_CHANNEL_ID`

2. Instale dependências:

```bash
python -m pip install -r requirements.txt
```

3. Inicialize e rode o bot:

```bash
python -m bot.main
```

## Importação YouTube (Fases 1 a 3.3)

1. Instale dependências adicionais:

```bash
python -m pip install -r requirements-yt.txt
```

2. Exporte todos os vídeos para CSV:

```bash
python -m scripts.youtube_export --channel-id UCxxxxxxxxxxxxxxxx
```

Isso gera `videos.csv`.

3. Crie seu arquivo de categorias:

```bash
copy categorias.json.example categorias.json
```

Edite `categorias.json` com equipamentos e tópicos válidos.

4. Categorize com IA e gere `videos_cat.csv`:

```bash
python -m scripts.youtube_categorize --categories categorias.json
```

5. Revise no Google Sheets:

- Importe `videos_cat.csv`
- Filtre por equipamento e ajuste os outliers

### Modo seguro (baixo risco de custo)

- Exportar só uma amostra:

```bash
python -m scripts.youtube_export --channel-id UCxxxxxxxxxxxxxxxx --max-pages 1 --limit 10
```

- Categorizar só alguns itens:

```bash
python -m scripts.youtube_categorize --categories categorias.json --limit 5
```

- Dry-run sem chamar a IA:

```bash
python -m scripts.youtube_categorize --categories categorias.json --limit 20 --dry-run
```

### Controle de custos

- YouTube API: limite quotas no Google Cloud Console do projeto.
- Anthropic: configure limites de gasto no painel da Anthropic e use `--limit` para testes.

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
