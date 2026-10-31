# Assistente de Agenda Pessoal

Aplicação web para organizar compromissos, tarefas e rotina pessoal, desenvolvida para uso próprio e executada localmente.

> **Status:** em desenvolvimento. Hoje a API permite cadastrar, listar, buscar, atualizar e excluir tarefas, com os dados salvos em um banco SQLite local, e conta com testes automatizados. Ainda não há interface gráfica.

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
- pytest e httpx2 (testes)
- Git e GitHub

## Estrutura do projeto

```
agenda-pessoal/
  backend/
    main.py              rotas da API e validação dos dados de entrada
    database.py          conexão com o banco, tabela e funções de acesso aos dados
  tests/
    conftest.py          banco temporário automático e cliente de testes
    test_*.py            testes da API, divididos por assunto
  data/                  criada automaticamente; guarda o agenda.db (não versionado)
  pytest.ini             configuração do pytest
  requirements.txt       dependências para rodar a API
  requirements-dev.txt   dependências de desenvolvimento (inclui as da API e as dos testes)
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

## Testes

Com o ambiente virtual ativo, instale as dependências de desenvolvimento e rode a suíte:

```powershell
pip install -r requirements-dev.txt
python -m pytest -v
```

Os testes cobrem o ciclo de vida das tarefas (cadastrar, listar, buscar, atualizar e excluir), os erros `404` para ids inexistentes e as validações de entrada (`422`).

Eles **nunca usam o banco real**: a cada teste, o banco é trocado por um arquivo temporário, criado e descartado pelo próprio `pytest`. Um teste específico vigia essa regra. Por isso o `data/agenda.db` não é lido nem alterado pela suíte.

## Limitações atuais

- Uso local e de um único usuário, sem autenticação.
- Os testes são executados manualmente, sem integração contínua.

## Princípios do projeto

- Nenhuma alteração relevante na agenda é aplicada sem autorização explícita do usuário.
- Alterações importantes são registradas em um histórico consultável.
- Gráficos usam apenas dados efetivamente registrados.
- Credenciais e informações pessoais nunca são publicadas neste repositório.
- Simplicidade e aprendizado vêm antes de complexidade.

## Próximas etapas (planejadas)

Categorias, prioridades e durações; histórico de alterações; relatórios; lembretes; interface gráfica. Nada disso está implementado ainda.

## Autor

Ariel
