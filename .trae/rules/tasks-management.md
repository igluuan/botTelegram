# Task Management

Você tem acesso a um arquivo `tasks.md` na raiz do projeto que funciona como inbox de tarefas.

## Regras

1. Ao receber o comando "executar tasks" ou "execute a task id:XXX", leia o `tasks.md` imediatamente.
2. Liste as tasks com status pending e pergunte ao usuário qual deseja executar, caso não tenha sido especificada.
3. Antes de implementar qualquer task:
   - Leia o contexto do projeto (arquivos existentes, estrutura de pastas)
   - Analise o escopo da task
   - Informe ao usuário o que pretende fazer e aguarde confirmação
4. Durante a implementação:
   - Implemente de forma incremental
   - Prefira editar arquivos existentes a criar novos, quando possível
   - Siga os padrões de código já presentes no projeto
5. Ao finalizar a implementação:
   - Pergunte ao usuário se está satisfeito com o resultado
   - Somente após confirmação, mova a task no `tasks.md` da seção `## Pending` para `## Done`, adicionando a data no formato `done: YYYY-MM-DD`
6. Se a task estiver escrita de forma ambígua ou vaga, pergunte ao usuário para detalhar antes de começar.
7. Nunca invente escopo além do que está descrito na task.

## Formato das tasks

Pending:

- [ ] id:001 | Descrição da task

Done:

- [x] id:001 | Descrição da task | done: 2025-02-20

## Como adicionar uma nova task

O usuário edita manualmente o `tasks.md` adicionando uma linha na seção `## Pending` seguindo o formato acima, incrementando o id.
