# Prompt de Construção — Bot Telegram de Arquivos e Links

---

## Contexto do Projeto

Você é um engenheiro de software sênior especializado em bots Telegram e automações em Python. Seu objetivo é construir um **MVP completo, funcional e bem estruturado** de um bot Telegram que permite ao administrador cadastrar arquivos e links organizados por categorias, e aos usuários navegar por menus interativos para receber esses conteúdos diretamente no chat.

---

## Stack Definida

| Camada | Tecnologia | Justificativa |
|---|---|---|
| Linguagem | Python 3.11+ | Ecossistema maduro para bots |
| Framework do Bot | `python-telegram-bot` v21 (async) | Biblioteca mais completa e mantida |
| Banco de Dados | SQLite via `aiosqlite` | Zero configuração, ideal para MVP |
| ORM / Queries | Raw SQL com `aiosqlite` | Simples e sem overhead |
| Armazenamento de Arquivos | Canal privado do Telegram | Gratuito, ilimitado, rápido |
| Variáveis de Ambiente | `python-dotenv` | Segurança para tokens e IDs |
| Hospedagem | Render.com (plano free) | Deploy gratuito via GitHub |
| Versionamento | Git + GitHub | CI/CD automático no Render |

---

## Arquitetura do Projeto

```
bot/
├── main.py                  # Ponto de entrada, registra handlers
├── config.py                # Carrega variáveis de ambiente
├── database.py              # Inicialização e queries do SQLite
├── handlers/
│   ├── user.py              # Handlers dos usuários (navegação, busca)
│   └── admin.py             # Handlers do admin (cadastro, remoção)
├── keyboards.py             # Todos os InlineKeyboardMarkup do bot
├── models.py                # Dataclasses: Category, Item
├── .env                     # TOKEN, ADMIN_ID, STORAGE_CHANNEL_ID
├── requirements.txt
└── README.md
```

---

## Schema do Banco de Dados

```sql
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    emoji TEXT DEFAULT '📁',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('file', 'link')),
    -- Para arquivos: message_id da mensagem no canal privado
    telegram_message_id INTEGER,
    -- Para links: a URL diretamente
    url TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Funcionalidades do MVP

### Para Usuários

- `/start` — Mensagem de boas-vindas com menu principal
- Navegação por categorias via botões inline
- Ao selecionar uma categoria, ver lista de itens disponíveis
- Receber arquivo (via forward do canal privado) ou link formatado
- `/buscar <termo>` — Busca por título em todas as categorias
- Botões de navegação "⬅️ Voltar" em todos os menus

### Para o Administrador

- `/admin` — Painel administrativo (somente para o ADMIN_ID configurado)
- `/addcategoria <emoji> <nome>` — Criar nova categoria
- `/addlink <categoria_id> <título> <url> [descrição]` — Adicionar link
- `/addfile <categoria_id> <título> [descrição>]` — Adicionar arquivo (bot aguarda o envio do arquivo no próximo passo, faz forward para o canal privado e salva o message_id)
- `/listar` — Listar todas as categorias e quantidade de itens
- `/deletar <item_id>` — Remover um item
- `/deletarcategoria <categoria_id>` — Remover categoria e todos seus itens

---

## Fluxo de Interação do Usuário

```
/start
└── 🏠 Menu Principal
    ├── 📂 Ver Categorias
    │   └── [Lista de categorias como botões]
    │       └── [Categoria selecionada]
    │           └── [Lista de itens como botões]
    │               └── [Item selecionado]
    │                   ├── Se arquivo → forward do canal privado
    │                   └── Se link → mensagem com botão "Abrir Link"
    └── 🔍 Buscar
        └── [Usuário digita termo]
            └── [Lista de resultados encontrados]
```

---

## Fluxo de Cadastro de Arquivo (Admin)

```
Admin envia: /addfile 1 "Manual da Impressora" "Manual completo HP DeskJet"
Bot responde: "✅ Agora envie o arquivo que deseja cadastrar."
Admin envia: [arquivo PDF]
Bot faz forward para o canal privado e salva o message_id
Bot responde: "✅ Arquivo cadastrado com sucesso! ID: 42"
```

---

## Regras de Implementação

1. **Toda operação de banco deve ser assíncrona** usando `aiosqlite` e `async/await`.
2. **Nunca armazene arquivos localmente** — sempre use o canal privado do Telegram como storage.
3. **Separação de responsabilidades** — handlers não devem ter lógica de banco; use funções em `database.py`.
4. **Verificação de admin** — qualquer handler em `admin.py` deve verificar `update.effective_user.id == ADMIN_ID` antes de executar.
5. **Tratamento de erros** — use `try/except` em todas as operações de banco e nas chamadas à API do Telegram.
6. **Mensagens amigáveis** — todas as respostas devem ter emoji e linguagem clara.
7. **ConversationHandler** — use para fluxos de múltiplos passos (ex: cadastrar arquivo em 2 etapas).

---

## Variáveis de Ambiente (.env)

```env
BOT_TOKEN=seu_token_aqui           # Token do BotFather
ADMIN_ID=123456789                 # Seu user_id no Telegram
STORAGE_CHANNEL_ID=-100123456789   # ID do canal privado de armazenamento
DATABASE_PATH=bot.db               # Caminho do arquivo SQLite
```

---

## Dependências (requirements.txt)

```
python-telegram-bot==21.6
aiosqlite==0.20.0
python-dotenv==1.0.1
```

---

## Exemplo de Código — Inicialização (main.py)

```python
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from config import BOT_TOKEN
from database import init_db
from handlers.user import start, show_categories, show_items, send_item, search
from handlers.admin import admin_panel, add_category, add_link, add_file_step1, add_file_step2, list_all, delete_item

WAITING_FILE = 1

async def main():
    await init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers de usuário
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buscar", search))
    app.add_handler(CallbackQueryHandler(show_categories, pattern="^categorias$"))
    app.add_handler(CallbackQueryHandler(show_items, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(send_item, pattern="^item_"))

    # Handlers de admin
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("addcategoria", add_category))
    app.add_handler(CommandHandler("addlink", add_link))
    app.add_handler(CommandHandler("listar", list_all))
    app.add_handler(CommandHandler("deletar", delete_item))

    # ConversationHandler para cadastro de arquivo
    conv = ConversationHandler(
        entry_points=[CommandHandler("addfile", add_file_step1)],
        states={WAITING_FILE: [MessageHandler(filters.Document.ALL | filters.PHOTO, add_file_step2)]},
        fallbacks=[]
    )
    app.add_handler(conv)

    print("🤖 Bot iniciado!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Critérios de Aceite do MVP

- [ ] Usuário consegue navegar por categorias e receber arquivos/links sem nenhum comando
- [ ] Admin consegue cadastrar categorias, links e arquivos via comandos
- [ ] Arquivos são armazenados no canal privado e entregues via forward
- [ ] Busca retorna resultados relevantes de qualquer categoria
- [ ] Bot funciona 24/7 hospedado no Render.com sem custo
- [ ] Banco de dados persiste entre reinicializações
- [ ] Código está organizado em módulos separados por responsabilidade

---

## Próximos Passos Pós-MVP (Backlog)

- Paginação na listagem de itens (quando houver muitos)
- Contagem de downloads por item
- Interface web simples para o admin cadastrar itens (Flask + HTMX)
- Integração com Google Sheets como fonte de dados alternativa
- Suporte a múltiplos idiomas (i18n)
- Notificação automática para usuários quando novo conteúdo é adicionado

---

*Prompt gerado para construção de MVP — Bot Telegram de Arquivos e Links*