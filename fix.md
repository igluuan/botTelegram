# Prompt — Auditoria de Segurança e Inconsistências do Projeto

---

Você é um engenheiro de segurança sênior especializado em auditoria de código Python.
Analise todos os arquivos do projeto e identifique **vulnerabilidades, inconsistências e riscos de vazamento de dados sensíveis**.

## O que verificar

### 1. Credenciais e chaves expostas
- Chaves de API hardcoded (`ANTHROPIC_API_KEY`, `BOT_TOKEN`, tokens Telegram)
- Senhas ou secrets em arquivos `.py`, `.env.example`, `config.py`, comentários ou logs
- Strings de conexão com credenciais embutidas
- Chaves commitadas acidentalmente (verificar se `.env` está no `.gitignore`)

### 2. Vazamento em logs
- `logger.info/debug/warning` imprimindo objetos que contenham tokens, IDs de usuário ou mensagens privadas
- F-strings em logs que expõem `settings.bot_token`, `settings.admin_id` ou similares
- Stack traces que imprimem variáveis sensíveis

### 3. Configuração e variáveis de ambiente
- Variáveis sensíveis sem validação de presença (`if not os.getenv(...)`)
- Fallbacks inseguros (`os.getenv("API_KEY", "default_key")`)
- Settings carregados de forma que exponham valores ao serializar o objeto

### 4. Banco de dados
- Queries com interpolação de string em vez de parâmetros (`f"WHERE id = {id}"` → SQL injection)
- Dados sensíveis de usuários (IDs, histórico) sem controle de acesso
- Ausência de validação de `user_id` antes de operações no banco

### 5. Handlers do Telegram
- Ausência de verificação `is_admin` em comandos privilegiados
- `update.effective_user` usado sem verificação de `None`
- `callback_query.data` processado sem sanitização

### 6. Requisições HTTP externas
- Tokens enviados em headers sem uso de HTTPS
- Ausência de timeout em chamadas `httpx`/`requests`
- Respostas de API logadas sem filtrar campos sensíveis

### 7. Arquivos e paths
- Paths construídos com input do usuário sem sanitização (`Path(user_input)`)
- Arquivos temporários criados sem controle de permissão
- `unknown_models.log` ou outros logs gravados em path público

---

## Formato de resposta esperado

Para cada problema encontrado, retorne:

```
[SEVERIDADE] Arquivo: caminho/do/arquivo.py — Linha X
Problema: descrição clara do risco
Correção: como resolver
```

Severidades: `CRÍTICO` | `ALTO` | `MÉDIO` | `BAIXO`

---

## Após o diagnóstico

- Aplique as correções diretamente nos arquivos afetados
- Para cada correção, mostre o diff (antes/depois)
- Gere um `.gitignore` adequado se não existir ou estiver incompleto
- Verifique se `.env` está listado no `.gitignore`
- Sugira uso de `python-dotenv` com validação obrigatória de variáveis críticas se não implementado

---

## Arquivos prioritários para análise

```
bot/config.py
bot/main.py
bot/handlers/admin.py
bot/handlers/user.py
bot/youtube/categorizer.py
bot/youtube/extractor.py
bot/scripts/sync_youtube.py
bot/db/connection.py
.env.example
.gitignore
```

Analise todos os arquivos disponíveis, não apenas os listados acima.