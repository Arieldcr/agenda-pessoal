# Assistente de Agenda Pessoal

Aplicação web para organizar compromissos, tarefas e rotina pessoal, desenvolvida para uso próprio e executada localmente.

> **Status:** em desenvolvimento. Hoje a API permite cadastrar e listar tarefas, com os dados salvos em um banco SQLite local. Ainda não há interface gráfica.

## Objetivo

Construir, de forma gradual, uma agenda pessoal com tarefas (duração, prioridade e categoria), atividades recorrentes, histórico de alterações, relatórios baseados em dados reais e lembretes. O projeto também é um exercício de aprendizado em desenvolvimento de software, organização de código e versionamento com Git.

## O que já funciona

- Cadastrar uma tarefa (`POST /tarefas`): título de 1 a 100 caracteres e descrição opcional.
- Listar as tarefas (`GET /tarefas`).
- Persistência: as tarefas ficam salvas em um banco SQLite local e continuam lá depois de reiniciar o servidor.
- Documentação interativa gerada automaticamente em `/docs`.

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
uvicorn backend.main:app --reload
```

Depois, abra http://127.0.0.1:8000/docs no navegador para testar a API. O banco é criado sozinho na primeira execução, em `data/agenda.db`.

Se o PowerShell bloquear a ativação do ambiente virtual, libere a execução de scripts apenas para o seu usuário:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## Princípios do projeto

- Nenhuma alteração relevante na agenda é aplicada sem autorização explícita do usuário.
- Alterações importantes são registradas em um histórico consultável.
- Gráficos usam apenas dados efetivamente registrados.
- Credenciais e informações pessoais nunca são publicadas neste repositório.
- Simplicidade e aprendizado vêm antes de complexidade.

## Próximas etapas (planejadas)

Buscar, editar e excluir tarefas; categorias, prioridades e durações; histórico de alterações; relatórios; lembretes. Nada disso está implementado ainda.

## Autor

Ariel
