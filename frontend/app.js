// ===== Configuração =====
const NOME_USUARIO = "Ariel";

// ===== Comunicação com a API: tudo passa por este objeto =====
const data = {
  async listar() {
    const resposta = await fetch("/tarefas");
    if (!resposta.ok) {
      throw new Error("Falha ao listar as tarefas");
    }
    return resposta.json();
  },
};

// ===== Tema claro e escuro =====
const CHAVE_TEMA = "kaizen-tema";

function lerTemaSalvo() {
  try {
    return localStorage.getItem(CHAVE_TEMA) || "escuro";
  } catch (erro) {
    return "escuro";
  }
}

function aplicarTema(tema) {
  document.documentElement.dataset.tema = tema;
  document
    .getElementById("botao-tema")
    .setAttribute("aria-checked", String(tema === "escuro"));
  try {
    localStorage.setItem(CHAVE_TEMA, tema);
  } catch (erro) {
    // Sem armazenamento disponível, o tema vale só para esta visita.
  }
}

function alternarTema() {
  const atual =
    document.documentElement.dataset.tema === "claro" ? "claro" : "escuro";
  aplicarTema(atual === "claro" ? "escuro" : "claro");
}

// ===== Cabeçalho: saudação, data e hora =====
const DIAS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];
const MESES = [
  "Jan",
  "Fev",
  "Mar",
  "Abr",
  "Mai",
  "Jun",
  "Jul",
  "Ago",
  "Set",
  "Out",
  "Nov",
  "Dez",
];

function saudacaoDaHora(hora) {
  if (hora < 12) {
    return "Bom dia";
  }
  if (hora < 18) {
    return "Boa tarde";
  }
  return "Boa noite";
}

function atualizarRelogio() {
  const agora = new Date();
  document.getElementById("saudacao").textContent =
    `${saudacaoDaHora(agora.getHours())}, ${NOME_USUARIO}!`;
  document.getElementById("data").textContent =
    `${DIAS[agora.getDay()]}, ${agora.getDate()} de ${MESES[agora.getMonth()]} de ${agora.getFullYear()}`;
  document.getElementById("hora").textContent = agora.toLocaleTimeString(
    "pt-BR",
    {
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}

function configurarAtalhoDeBusca() {
  document.addEventListener("keydown", (evento) => {
    if (
      (evento.ctrlKey || evento.metaKey) &&
      evento.key.toLowerCase() === "k"
    ) {
      evento.preventDefault();
      document.getElementById("busca").focus();
    }
  });
}

// ===== Indicadores: sempre calculados a partir da lista de tarefas =====
function calcularIndicadores(tarefas) {
  const total = tarefas.length;
  const concluidas = tarefas.filter((tarefa) => tarefa.concluida).length;
  return { total, concluidas, pendentes: total - concluidas };
}

function mostrarIndicadores(indicadores) {
  document.getElementById("kpi-total").textContent = indicadores.total;
  document.getElementById("kpi-concluidas").textContent =
    indicadores.concluidas;
  document.getElementById("kpi-pendentes").textContent = indicadores.pendentes;
}

// ===== Início =====
async function iniciar() {
  aplicarTema(lerTemaSalvo());
  document.getElementById("botao-tema").addEventListener("click", alternarTema);

  atualizarRelogio();
  setInterval(atualizarRelogio, 15000);
  configurarAtalhoDeBusca();

  const estado = document.getElementById("estado");
  try {
    const tarefas = await data.listar();
    mostrarIndicadores(calcularIndicadores(tarefas));
    estado.textContent = `Conexão com a API funcionando: ${tarefas.length} tarefa(s) no banco.`;
  } catch (erro) {
    estado.textContent = "Não foi possível falar com a API.";
  }
}

iniciar();
