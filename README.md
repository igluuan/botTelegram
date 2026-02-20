# Bot Telegram de Arquivos, Links e Tutoriais (Helpdesk)

Bot Telegram em Python projetado para gerenciar uma base de conhecimento de arquivos, manuais e vídeos tutoriais. O sistema permite cadastro manual (admin), sincronização automática com canais do YouTube e navegação intuitiva para usuários finais.

## 🚀 Visão Geral

- **Organização por Categorias**: Navegação via menus inline com paginação.
- **Sincronização com YouTube**: Importação automática de vídeos de canais ou playlists, com extração de metadados.
- **Categorização Inteligente**: Uso da API Anthropic (Claude) para classificar automaticamente vídeos por **Marca**, **Modelo**, **Tipo de Problema** e **Nível de Dificuldade**.
- **Busca Poderosa**: Pesquisa global por termos ou filtrada por categoria.
- **Favoritos e Histórico**: Acesso rápido aos itens mais utilizados pelos usuários.
- **Armazenamento Seguro**: Arquivos físicos (PDFs, firmwares) são armazenados em um canal privado do Telegram.

## 📋 Requisitos

- Python 3.11+
- FFmpeg (necessário para o `yt-dlp` processar metadados de vídeos)
- Token de Bot do Telegram
- Chave de API da Anthropic (opcional, para categorização automática)

## ⚙️ Configuração

1. Crie um arquivo `.env` na raiz (use `.env.example` como base):

```env
# Telegram
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
ADMIN_ID=123456789
STORAGE_CHANNEL_ID=-1001234567890

# Banco de Dados
DATABASE_PATH=bot.db

# Integrações Opcionais
ANTHROPIC_API_KEY=sk-ant-... (Para categorização via IA)
```

2. Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

3. Inicialize o bot:

```bash
python -m bot.main
```

## 🛠️ Ferramentas e Scripts

O projeto inclui scripts utilitários para manutenção e importação de conteúdo. Execute-os a partir da raiz do projeto:

### 1. Sincronização com YouTube
Importa vídeos de um canal ou playlist, categoriza usando IA e publica no canal de storage.

```bash
# Sincronizar um canal/playlist específico
python -m bot.scripts.sync_youtube https://www.youtube.com/@CanalExemplo

# Opções úteis:
# --force-update: Atualiza metadados de vídeos já importados
# --limit 10: Importa apenas os 10 vídeos mais recentes
# --dry-run: Simula a importação sem gravar no banco
```

### 2. Limpeza de Duplicatas
Remove vídeos duplicados do banco de dados, mantendo apenas o registro mais antigo.

```bash
python -m bot.scripts.cleanup_youtube_duplicates --apply
```

### 3. Padronização de Modelos
Aplica regras de Regex para padronizar nomes de modelos (ex: "L6902" -> "MFC-L6902DW") e marcas.

```bash
python -m bot.scripts.fix_modelos
```

## 📱 Uso do Bot

### Comandos de Usuário
- `/start`: Abre o menu principal de navegação.
- `/buscar <termo>`: Pesquisa itens em toda a base.
- `/buscarcat <cat_id> <termo>`: Pesquisa dentro de uma categoria específica.
- Navegação via botões: Explorar categorias, ver itens recentes e favoritos.

### Comandos de Administrador
- `/admin`: Painel de controle.
- `/addcategoria <emoji> <nome>`: Cria uma nova categoria manualmente.
- `/addlink <cat_id> <título> <url>`: Adiciona um link externo.
- `/addfile`: Inicia o fluxo de upload de arquivo (PDF/Zip) para o canal de storage.
- `/deletar <id>`: Remove um item.
- `/listar`: Exibe estatísticas das categorias.

## 💾 Estrutura de Dados

O banco de dados SQLite (`bot.db`) gerencia:
- **Categories**: Agrupamentos lógicos (ex: Brother, Kyocera, Samsung).
- **Items**: Conteúdo real, podendo ser:
  - `file`: Documento armazenado no Telegram.
  - `link`: URL externa ou vídeo do YouTube.
  - Metadados ricos: `marca`, `modelo`, `video_id`, `description`.
- **User Data**: Favoritos e histórico de acesso.

## 🧪 Testes

Para executar a suíte de testes:

```bash
# Instalar dependências de dev
python -m pip install -r requirements-dev.txt

# Rodar testes
python -m pytest
```
