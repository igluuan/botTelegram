# Plano de Correções e Melhorias (Code Review)

Baseado na revisão de código realizada, este plano visa corrigir bugs de UX, melhorar a robustez do código e refatorar trechos repetitivos.

## 1. Correção na Normalização da Busca (Bug/UX)

**Problema:** A normalização atual `re.sub(r"[\s\-]", "", term)` remove *todos* os espaços. Busca por "toner brother" vira "tonerbrother", que não encontra "Toner Brother" no banco.

**Solução:** Substituir múltiplos espaços/hífens por um único espaço.

**Arquivo:** `bot/handlers/user.py`

```python
# Antes
term_norm = re.sub(r"[\s\-]", "", term).lower()

# Depois
term_norm = re.sub(r"[\s\-]+", " ", term).strip().lower()
```

---

## 2. Refatoração de Keyboards (DRY)

**Problema:** Lógica de paginação duplicada em `categories_menu`, `items_menu` e `paginated_items_menu`.

**Solução:** Criar uma função auxiliar privada para gerar a linha de botões de paginação.

**Arquivo:** `bot/ui/keyboards.py`

```python
def _build_pagination_row(page: int, total_pages: int, callback_prefix: str) -> list[InlineKeyboardButton]:
    row = []
    if page > 1:
        row.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"{callback_prefix}_{page - 1}"))
    
    if total_pages > 1:
        row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
        
    if page < total_pages:
        row.append(InlineKeyboardButton("Próxima ➡️", callback_data=f"{callback_prefix}_{page + 1}"))
    return row
```

---

## 3. Robustez no Parsing de Callback (Bug Potencial)

**Problema:** Em `show_items_by_subcat`, a separação `raw_sub.rsplit("_", 1)` assume que qualquer underscore final é paginação. Se a subcategoria for "wi_fi", isso pode falhar.

**Solução:** Usar um separador mais explícito ou validar se o sufixo é realmente um número.

**Arquivo:** `bot/handlers/user.py`

```python
def _parse_subcat_callback(data: str) -> tuple[str, str, int]:
    # data: "subcat|Marca|Subcategoria" ou "subcat|Marca|Subcategoria_2"
    parts = data.split("|")
    if len(parts) < 3:
        raise ValueError("Dados inválidos")
    
    marca = parts[1]
    raw_sub = parts[2]
    page = 1
    
    # Verifica se termina com _\d+
    match = re.search(r"^(.*)_(\d+)$", raw_sub)
    if match:
        subcategoria = match.group(1)
        page = int(match.group(2))
    else:
        subcategoria = raw_sub
        
    return marca, subcategoria, page
```

---

## 4. Ordem de Execução

1.  [ ] **Refatorar Keyboards**: Implementar `_build_pagination_row` e usar nas funções de menu.
2.  [ ] **Corrigir Handler de Busca**: Ajustar regex de normalização.
3.  [ ] **Refatorar Handler de Subcategoria**: Extrair parsing para função auxiliar e corrigir lógica de underscore.
