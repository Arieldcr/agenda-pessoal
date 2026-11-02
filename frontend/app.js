// Toda a conversa com a API fica neste objeto.
const data = {
  async listar() {
    const resposta = await fetch("/tarefas");
    if (!resposta.ok) {
      throw new Error("Falha ao listar as tarefas");
    }
    return resposta.json();
  },
};

async function iniciar() {
  const estado = document.getElementById("estado");
  try {
    const tarefas = await data.listar();
    estado.textContent = `Conexão com a API funcionando: ${tarefas.length} tarefa(s) no banco.`;
  } catch (erro) {
    estado.textContent = "Não foi possível falar com a API.";
  }
}

iniciar();
