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
  if (hora < 5) {
    return "Boa madrugada";
  }
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

// ===== Lista de tarefas =====
const ICONE_CHECK =
  '<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 6.5l2.5 2.5 4.5-5"/></svg>';

function criarItem(tarefa) {
  const item = document.createElement("li");
  item.className = tarefa.concluida ? "item concluida" : "item";

  const marca = document.createElement("span");
  marca.className = "marca";
  marca.setAttribute("role", "img");
  marca.setAttribute("aria-label", tarefa.concluida ? "Concluída" : "Pendente");
  if (tarefa.concluida) {
    marca.innerHTML = ICONE_CHECK;
  }

  const corpo = document.createElement("div");
  const titulo = document.createElement("strong");
  titulo.className = "titulo";
  titulo.textContent = tarefa.titulo;
  corpo.appendChild(titulo);

  if (tarefa.descricao) {
    const descricao = document.createElement("small");
    descricao.className = "descricao";
    descricao.textContent = tarefa.descricao;
    corpo.appendChild(descricao);
  }

  item.append(marca, corpo);
  return item;
}

let tarefasCarregadas = [];
let filtroAtual = "todas";
let termoBusca = "";

function normalizar(texto) {
  return texto
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function mostrarLista() {
  const termo = normalizar(termoBusca.trim());
  const visiveis = tarefasCarregadas.filter((tarefa) => {
    if (filtroAtual === "pendentes" && tarefa.concluida) return false;
    if (filtroAtual === "concluidas" && !tarefa.concluida) return false;
    if (!termo) return true;
    return normalizar(`${tarefa.titulo} ${tarefa.descricao || ""}`).includes(
      termo,
    );
  });
  const ordenadas = [...visiveis].sort(
    (a, b) => Number(a.concluida) - Number(b.concluida) || a.id - b.id,
  );
  document.getElementById("lista").replaceChildren(...ordenadas.map(criarItem));
}

function mostrarContadores() {
  const { total, concluidas, pendentes } =
    calcularIndicadores(tarefasCarregadas);
  document.getElementById("cont-todas").textContent = total;
  document.getElementById("cont-pendentes").textContent = pendentes;
  document.getElementById("cont-concluidas").textContent = concluidas;
}

function configurarFiltros() {
  const botoes = document.querySelectorAll(".filtro");
  botoes.forEach((botao) => {
    botao.addEventListener("click", () => {
      filtroAtual = botao.dataset.filtro;
      botoes.forEach((outro) => {
        const ativo = outro === botao;
        outro.classList.toggle("ativo", ativo);
        outro.setAttribute("aria-pressed", String(ativo));
      });
      mostrarLista();
    });
  });
}

// ===== Calendário =====
const MESES_COMPLETOS = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];
const INICIAIS_DIAS = ["D", "S", "T", "Q", "Q", "S", "S"];
let mesExibido = new Date(new Date().getFullYear(), new Date().getMonth(), 1);

function mostrarCalendario() {
  const ano = mesExibido.getFullYear();
  const mes = mesExibido.getMonth();
  document.getElementById("titulo-mes").textContent =
    `${MESES_COMPLETOS[mes]} de ${ano}`;

  const celulas = INICIAIS_DIAS.map((letra) => {
    const cabecalho = document.createElement("span");
    cabecalho.className = "dia-semana";
    cabecalho.textContent = letra;
    return cabecalho;
  });

  const hoje = new Date().toDateString();
  const deslocamento = new Date(ano, mes, 1).getDay();
  for (let i = 0; i < 42; i++) {
    const dia = new Date(ano, mes, 1 - deslocamento + i);
    const celula = document.createElement("span");
    celula.className = "dia";
    if (dia.getMonth() !== mes) celula.classList.add("fora");
    if (dia.toDateString() === hoje) celula.classList.add("hoje");
    celula.textContent = dia.getDate();
    celulas.push(celula);
  }
  document.getElementById("grade").replaceChildren(...celulas);
}

function mudarMes(delta) {
  mesExibido = new Date(
    mesExibido.getFullYear(),
    mesExibido.getMonth() + delta,
    1,
  );
  mostrarCalendario();
}

// ===== Painel Sobre seus assuntos =====
function mostrarProgresso() {
  const { total, concluidas } = calcularIndicadores(tarefasCarregadas);
  const percentual = total === 0 ? 0 : Math.round((concluidas / total) * 100);
  const anel = document.getElementById("anel");
  anel.style.setProperty("--percentual", `${percentual}%`);
  anel.setAttribute("aria-label", `Progresso geral: ${percentual}%`);
  document.getElementById("anel-valor").textContent = `${percentual}%`;
  document.getElementById("anel-texto").textContent =
    `${concluidas} de ${total} concluídas`;
}
// ===== Estados: carregando, erro e vazio =====
function mostrarAviso(texto, erro = false) {
  const aviso = document.getElementById("estado");
  aviso.textContent = texto;
  aviso.classList.toggle("erro", erro);
  aviso.hidden = texto === "";
}

async function carregarTarefas() {
  const botao = document.getElementById("tentar-novamente");
  botao.hidden = true;
  mostrarAviso("Carregando tarefas...");
  try {
    tarefasCarregadas = await data.listar();
  } catch (erro) {
    mostrarAviso(
      "Não foi possível carregar as tarefas. Verifique se o servidor está rodando.",
      true,
    );
    botao.hidden = false;
    return;
  }
  mostrarIndicadores(calcularIndicadores(tarefasCarregadas));
  mostrarContadores();
  mostrarProgresso();
  mostrarLista();
}
// ===== Início =====
async function iniciar() {
  aplicarTema(lerTemaSalvo());
  document.getElementById("botao-tema").addEventListener("click", alternarTema);

  atualizarRelogio();
  setInterval(atualizarRelogio, 15000);
  configurarAtalhoDeBusca();
  configurarFiltros();

  mostrarCalendario();
  document
    .getElementById("mes-anterior")
    .addEventListener("click", () => mudarMes(-1));
  document
    .getElementById("mes-seguinte")
    .addEventListener("click", () => mudarMes(1));

  document.getElementById("busca").addEventListener("input", (evento) => {
    termoBusca = evento.target.value;
    mostrarLista();
    if (tarefasCarregadas.length === 0) {
      mostrarAviso("Nenhuma tarefa cadastrada ainda.");
    } else if (ordenadas.length === 0) {
      mostrarAviso("Nenhuma tarefa encontrada com esse filtro ou busca.");
    } else {
      mostrarAviso("");
    }
  });

  document
    .getElementById("tentar-novamente")
    .addEventListener("click", carregarTarefas);
  await carregarTarefas();
}

iniciar();
