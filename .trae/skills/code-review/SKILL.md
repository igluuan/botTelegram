---
name: code-review
description: Use quando precisar revisar código Python, apontando bugs, segurança, performance e boas práticas.
---

# Code Review — Python

## O que fazer

Ao revisar o código fornecido, analise e reporte nos seguintes aspectos, na ordem abaixo:

### 1. Bugs e Erros Lógicos
- Identifique erros que causam comportamento incorreto ou exceções não tratadas.
- Aponte variáveis não inicializadas, comparações erradas, loops infinitos, etc.

### 2. Segurança
- Verifique exposição de credenciais ou dados sensíveis.
- Identifique inputs não sanitizados, injeção de SQL, uso inseguro de `eval()`/`exec()`.
- Aponte dependências desatualizadas ou com vulnerabilidades conhecidas.

### 3. Performance
- Identifique operações desnecessárias dentro de loops.
- Sugira uso de list comprehensions, generators ou estruturas mais eficientes.
- Aponte queries N+1 ou chamadas redundantes a banco/API.

### 4. Boas Práticas (PEP 8 + SOLID)
- Verifique nomenclatura: `snake_case` funções/variáveis, `PascalCase` classes.
- Funções com mais de uma responsabilidade devem ser sinalizadas.
- Funções públicas sem docstring devem ser sinalizadas.
- Remova `print` e debug statements — use `logging`.

### 5. Cobertura de Testes
- Verifique se a lógica crítica possui testes.
- Sugira casos de teste ausentes (edge cases, exceções esperadas).

---

## Formato da resposta

Para cada problema encontrado, responda no formato:

```
[CATEGORIA] Linha X — descrição do problema
➜ Sugestão: como corrigir
```

Categorias: `BUG` `SEGURANÇA` `PERFORMANCE` `PADRÃO` `TESTE`

Ao final, dê uma nota geral de **1 a 10** com um resumo de 1 linha.

---

## Exemplo de saída

```
[BUG] Linha 12 — variável `result` pode ser None antes de ser retornada
➜ Sugestão: adicionar verificação `if result is None: raise ValueError(...)`

[SEGURANÇA] Linha 34 — input do usuário usado diretamente na query SQL
➜ Sugestão: usar parâmetros preparados com `cursor.execute(query, (param,))`

[PADRÃO] Linha 56 — função `processData` não segue snake_case
➜ Sugestão: renomear para `process_data`

Nota geral: 6/10 — código funcional mas com risco de segurança crítico na linha 34.
```