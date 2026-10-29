# Assistente de Agenda Pessoal

Aplicação web para organizar compromissos, tarefas e rotina pessoal, desenvolvida para uso próprio e executada localmente.

> **Status:** em desenvolvimento. Hoje a API permite cadastrar, listar, buscar, atualizar e excluir tarefas, com os dados salvos em um banco SQLite local. Ainda não há interface gráfica.

## Objetivo

Construir, de forma gradual, uma agenda pessoal com tarefas (duração, prioridade e categoria), atividades recorrentes, histórico de alterações, relatórios baseados em dados reais e lembretes. O projeto também é um exercício de aprendizado em desenvolvimento de software, organização de código e versionamento com Git.

## O que já funciona

Cada tarefa tem `id`, `titulo`, `descricao` (opcional) e `concluida`. A API oferece:

| Operação      | Rota                   | Sucesso                                         | Erros                                                   |
| ------------- | ---------------------- | ----------------------------------------------- | ------------------------------------------------------- |
| Cadastrar     | `POST /tarefas`        | `201` com a tarefa criada                       | `422` se os dados forem inválidos                       |
| Listar        | `GET /tarefas`         | `200` com a lista (vazia se não houver tarefas) |                                                         |
| Buscar por id | `GET /tarefas/{id}`    | `200` com a tarefa                              | `404` se não existir                                    |
| Atualizar     | `PATCH /tarefas/{id}`  | `200` com a tarefa atualizada                   | `404` se não existir; `422` se os dados forem inválidos |
| Excluir       | `DELETE /tarefas/{id}` | `204`, sem corpo                                | `404` se não existir                                    |

Regras:

- O título tem de 1 a 100 caracteres, e espaços no começo e no fim são removidos.
- A tarefa nasce com `concluida = false`. Para marcá-la como concluída, use `PATCH` com `{"concluida": true}`.
- O `PATCH` é parcial: só os campos enviados mudam. O `id` não pode ser alterado.
- Os dados continuam salvos depois de reiniciar o servidor.
- A documentação interativa é gerada automaticamente em `/docs`.

## Tecnologias

- Python 3.12
- FastAPI e Uvicorn
- SQLModel e SQLite
- Git e GitHub

## Estrutura do projeto

```
agenda-pessoal/
  backend/
    main.py        rotas da API e validação dos dados de entrada
    database.py    conexão com o banco, tabela e funções de acesso aos dados
  data/            criada automaticamente; guarda o agenda.db (não versionado)
  requirements.txt
  README.md
```

## Como executar (Windows, PowerShell)

Pré-requisitos: Python 3.12 e Git.

```powershell
git clone https://github.com/Arieldcr/agenda-pessoal.git
cd agenda-pessoal
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

Depois, abra http://127.0.0.1:8000/docs no navegador para testar a API. O banco é criado sozinho na primeira execução, em `data/agenda.db`.

Se o PowerShell bloquear a ativação do ambiente virtual, libere a execução de scripts apenas para o seu usuário:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Para estudar o SQL gerado, troque `MOSTRAR_SQL` para `True` em `backend/database.py` (e volte para `False` depois).

## Limitações atuais

- Uso local e de um único usuário, sem autenticação.
- Não há testes automatizados: as operações foram testadas manualmente pela documentação interativa.

## Princípios do projeto

- Nenhuma alteração relevante na agenda é aplicada sem autorização explícita do usuário.
- Alterações importantes são registradas em um histórico consultável.
- Gráficos usam apenas dados efetivamente registrados.
- Credenciais e informações pessoais nunca são publicadas neste repositório.
- Simplicidade e aprendizado vêm antes de complexidade.

## Próximas etapas (planejadas)

Categorias, prioridades e durações; histórico de alterações; relatórios; lembretes; interface gráfica; testes automatizados. Nada disso está implementado ainda.

## Autor

Ariel
