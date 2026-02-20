# Project Rules

- Linguagem: Python. Siga a PEP 8 para estilo e formatação.
- Respeite a estrutura de pastas existente. Não altere arquivos fora do escopo da tarefa.
- Nomes em inglês: `snake_case` variáveis e funções, `PascalCase` classes, `UPPER_SNAKE_CASE` constantes.
- Funções pequenas, responsabilidade única. Use docstrings em funções públicas.
- Nunca deixe `print` ou debug statements no código final — use `logging`.
- Nunca exponha credenciais no código — use `.env` com `python-dotenv`.
- Sempre valide e sanitize inputs do usuário.
- Commits no padrão Conventional Commits: `tipo(escopo): descrição`.