// ===== Configuração =====
const NOME_USUARIO = "Ariel";
const PALETA = [
  "#2563ff",
  "#16c79a",
  "#8b5cf6",
  "#f5b324",
  "#38bdf8",
  "#ef4444",
];
const ROTULOS_DE_CAMPO = {
  titulo: "Título",
  descricao: "Descrição",
  dia: "Dia",
  hora: "Hora",
  duracao_min: "Duração",
  prioridade: "Prioridade",
  categoria: "Categoria",
  frequencia: "Repetição",
  intervalo: "Intervalo",
  dias_semana: "Dias da semana",
  dia_do_mes: "Dia do mês",
  inicio: "Início",
  fim: "Término",
};
const ROTULOS_DE_PRIORIDADE = { alta: "Alta", media: "Média", baixa: "Baixa" };

// ===== Comunicação com a API: tudo passa por este objeto =====
async function mensagemDeErro(resposta, padrao) {
  if (resposta.status !== 422) {
    return padrao;
  }
  try {
    const corpo = await resposta.json();
    if (typeof corpo.detail === "string") {
      return corpo.detail;
    }
    const item = corpo.detail[0];
    const campo = item.loc[item.loc.length - 1];
    if (ROTULOS_DE_CAMPO[campo]) {
      return `Confira o campo ${ROTULOS_DE_CAMPO[campo]}.`;
    }
    return item.msg.replace("Value error, ", "");
  } catch (erro) {
    return padrao;
  }
}

async function enviar(metodo, url, corpo, padrao) {
  const opcoes = { method: metodo };
  if (corpo !== undefined) {
    opcoes.headers = { "Content-Type": "application/json" };
    opcoes.body = JSON.stringify(corpo);
  }
  const resposta = await fetch(url, opcoes);
  if (!resposta.ok) {
    throw new Error(await mensagemDeErro(resposta, padrao));
  }
  return resposta.status === 204 ? null : resposta.json();
}

const data = {
  listar() {
    return enviar("GET", "/tarefas", undefined, "Falha ao listar as tarefas");
  },

  agenda(de, ate, semDia = false) {
    const consulta = new URLSearchParams({ de, ate });
    if (semDia) {
      consulta.set("sem_dia", "true");
    }
    return enviar(
      "GET",
      `/agenda?${consulta}`,
      undefined,
      "Falha ao consultar a agenda",
    );
  },

  criar(campos) {
    return enviar(
      "POST",
      "/tarefas",
      campos,
      "Não foi possível cadastrar a tarefa.",
    );
  },

  atualizar(id, campos) {
    return enviar(
      "PATCH",
      `/tarefas/${id}`,
      campos,
      "Não foi possível atualizar a tarefa.",
    );
  },

  async excluir(id) {
    const resposta = await fetch(`/tarefas/${id}`, { method: "DELETE" });
    if (!resposta.ok && resposta.status !== 404) {
      throw new Error("Não foi possível excluir a tarefa.");
    }
  },

  buscarRecorrencia(id) {
    return enviar(
      "GET",
      `/recorrencias/${id}`,
      undefined,
      "Não foi possível abrir a recorrência.",
    );
  },

  criarRecorrencia(campos) {
    return enviar(
      "POST",
      "/recorrencias",
      campos,
      "Não foi possível cadastrar a tarefa recorrente.",
    );
  },

  atualizarRecorrencia(id, campos) {
    return enviar(
      "PATCH",
      `/recorrencias/${id}`,
      campos,
      "Não foi possível atualizar a tarefa recorrente.",
    );
  },

  async excluirRecorrencia(id) {
    const resposta = await fetch(`/recorrencias/${id}`, { method: "DELETE" });
    if (!resposta.ok && resposta.status !== 404) {
      throw new Error("Não foi possível excluir a tarefa recorrente.");
    }
  },

  salvarOcorrencia(recorrenciaId, dia, campos) {
    return enviar(
      "PUT",
      `/recorrencias/${recorrenciaId}/ocorrencias/${dia}`,
      campos,
      "Não foi possível alterar a ocorrência.",
    );
  },

  alterarASeguir(recorrenciaId, dia, campos) {
    return enviar(
      "PATCH",
      `/recorrencias/${recorrenciaId}/a-partir-de/${dia}`,
      campos,
      "Não foi possível alterar as próximas ocorrências.",
    );
  },

  async excluirASeguir(recorrenciaId, dia) {
    const resposta = await fetch(
      `/recorrencias/${recorrenciaId}/a-partir-de/${dia}`,
      { method: "DELETE" },
    );
    if (!resposta.ok && resposta.status !== 404) {
      throw new Error("Não foi possível excluir as próximas ocorrências.");
    }
  },
};

// ===== Estado da tela =====
let tarefasCarregadas = []; // tarefas avulsas: indicadores do topo
let itensAgenda = []; // agenda da grade do calendário, com as tarefas sem dia
let itensSemana = []; // agenda da semana atual
let filtroAtual = "todas";
let termoBusca = "";
let diaSelecionado = null;
let modoDoDialogo = "nova";
let itemEmEdicao = null;
let mesExibido = new Date(new Date().getFullYear(), new Date().getMonth(), 1);

// ===== Utilitários =====
function criarElemento(tag, classe, texto) {
  const elemento = document.createElement(tag);
  if (classe) {
    elemento.className = classe;
  }
  if (texto !== undefined) {
    elemento.textContent = texto;
  }
  return elemento;
}

function normalizar(texto) {
  return texto
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function doisDigitos(numero) {
  return String(numero).padStart(2, "0");
}

function chaveDoDia(dia) {
  return `${dia.getFullYear()}-${doisDigitos(dia.getMonth() + 1)}-${doisDigitos(dia.getDate())}`;
}

function paraData(chave) {
  const [ano, mes, dia] = chave.split("-").map(Number);
  return new Date(ano, mes - 1, dia);
}

function rotuloDoDia(chave) {
  const agora = new Date();
  const hoje = new Date(agora.getFullYear(), agora.getMonth(), agora.getDate());
  const dia = paraData(chave);
  const diferenca = Math.round((dia - hoje) / 86400000);
  if (diferenca === 0) return "Hoje";
  if (diferenca === 1) return "Amanhã";
  if (diferenca === -1) return "Ontem";
  return `${DIAS[dia.getDay()]}, ${doisDigitos(dia.getDate())}/${doisDigitos(dia.getMonth() + 1)}`;
}

function formatarDuracao(minutos) {
  if (minutos < 60) {
    return `${minutos} min`;
  }
  const horas = Math.floor(minutos / 60);
  const resto = minutos % 60;
  return resto ? `${horas}h${doisDigitos(resto)}` : `${horas}h`;
}

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

// ===== Indicadores do topo e progresso do dia =====
function calcularIndicadores(itens) {
  const total = itens.length;
  const concluidas = itens.filter((item) => item.concluida).length;
  return { total, concluidas, pendentes: total - concluidas };
}

function mostrarIndicadores() {
  const indicadores = calcularIndicadores(tarefasCarregadas);
  document.getElementById("kpi-total").textContent = indicadores.total;
  document.getElementById("kpi-concluidas").textContent =
    indicadores.concluidas;
  document.getElementById("kpi-pendentes").textContent = indicadores.pendentes;
  document.getElementById("kpi-semana").textContent = itensSemana.length;
}

function chaveDoDiaEmFoco() {
  return diaSelecionado || chaveDoDia(new Date());
}

function mostrarProgresso() {
  const chave = chaveDoDiaEmFoco();
  const { total, concluidas } = calcularIndicadores(itensDoDia(chave));
  const rotulo = document.querySelector(".progresso .legenda span");
  if (rotulo) {
    rotulo.textContent = `Progresso: ${rotuloDoDia(chave)}`;
  }
  const percentual = total === 0 ? 0 : Math.round((concluidas / total) * 100);
  const anel = document.getElementById("anel");
  anel.style.setProperty("--percentual", `${percentual}%`);
  anel.setAttribute("aria-label", `Progresso geral: ${percentual}%`);
  document.getElementById("anel-valor").textContent = `${percentual}%`;
  document.getElementById("anel-texto").textContent =
    `${concluidas} de ${total} concluídas`;
}

// ===== Painel Sobre seus assuntos: categorias e resumo do dia =====
function mostrarAssuntos() {
  const alvo = document.getElementById("assuntos");
  const contagem = new Map();
  itensDoDia(chaveDoDiaEmFoco()).forEach((tarefa) => {
    if (!tarefa.categoria) {
      return;
    }
    const chave = normalizar(tarefa.categoria);
    const grupo = contagem.get(chave) || { nome: tarefa.categoria, total: 0 };
    grupo.total += 1;
    contagem.set(chave, grupo);
  });
  const grupos = [...contagem.values()].sort(
    (a, b) => b.total - a.total || a.nome.localeCompare(b.nome),
  );

  if (grupos.length === 0) {
    alvo.replaceChildren(
      criarElemento(
        "p",
        "vazio-nota",
        "Por assunto: sem tarefas com categoria neste dia.",
      ),
    );
    return;
  }

  const soma = grupos.reduce((acumulado, grupo) => acumulado + grupo.total, 0);
  let inicio = 0;
  const fatias = [];
  const itens = grupos.map((grupo, indice) => {
    const cor = PALETA[indice % PALETA.length];
    const fim = inicio + (grupo.total / soma) * 100;
    fatias.push(`${cor} ${inicio}% ${fim}%`);
    inicio = fim;
    const item = criarElemento("li");
    const ponto = criarElemento("i");
    ponto.style.background = cor;
    item.append(
      ponto,
      criarElemento("span", "", `${grupo.nome}: ${grupo.total}`),
    );
    return item;
  });

  const rosca = criarElemento("div", "rosca");
  rosca.style.background = `conic-gradient(${fatias.join(", ")})`;
  rosca.append(criarElemento("span", "", String(soma)));
  const legenda = criarElemento("ul", "legenda-assuntos");
  legenda.append(...itens);
  alvo.replaceChildren(rosca, legenda);
}

function itensDoDia(chave) {
  const vistos = new Map();
  [...itensAgenda, ...itensSemana].forEach((item) => {
    if (item.dia === chave) {
      vistos.set(item.id, item);
    }
  });
  return [...vistos.values()];
}

function mostrarResumoDoDia() {
  const alvo = document.getElementById("resumo-dia");
  const chave = diaSelecionado || chaveDoDia(new Date());
  const doDia = itensDoDia(chave);
  const titulo = criarElemento(
    "strong",
    "",
    `Resumo do dia: ${rotuloDoDia(chave)}`,
  );

  if (doDia.length === 0) {
    alvo.replaceChildren(
      titulo,
      criarElemento("span", "", "Nenhuma tarefa neste dia."),
    );
    return;
  }

  const concluidas = doDia.filter((item) => item.concluida).length;
  const minutos = doDia.reduce(
    (soma, item) => soma + (item.duracao_min || 0),
    0,
  );
  const barra = criarElemento("div", "barra");
  const preenchimento = criarElemento("i");
  preenchimento.style.width = `${Math.round((concluidas / doDia.length) * 100)}%`;
  barra.appendChild(preenchimento);
  let texto = `${concluidas} de ${doDia.length} concluídas`;
  if (minutos > 0) {
    texto += ` · ${formatarDuracao(minutos)} planejadas`;
  }
  alvo.replaceChildren(titulo, barra, criarElemento("span", "", texto));
}

// ===== Avisos da lista: carregando, erro e vazio =====
function mostrarAviso(texto, erro = false) {
  const aviso = document.getElementById("estado");
  aviso.textContent = texto;
  aviso.classList.toggle("erro", erro);
  aviso.hidden = texto === "";
}

function janelaDaGrade() {
  const primeiro = new Date(mesExibido.getFullYear(), mesExibido.getMonth(), 1);
  const inicio = new Date(
    primeiro.getFullYear(),
    primeiro.getMonth(),
    1 - primeiro.getDay(),
  );
  const fim = new Date(
    inicio.getFullYear(),
    inicio.getMonth(),
    inicio.getDate() + 41,
  );
  return { de: chaveDoDia(inicio), ate: chaveDoDia(fim) };
}

function janelaDaSemana() {
  const hoje = new Date();
  const domingo = new Date(
    hoje.getFullYear(),
    hoje.getMonth(),
    hoje.getDate() - hoje.getDay(),
  );
  const sabado = new Date(
    domingo.getFullYear(),
    domingo.getMonth(),
    domingo.getDate() + 6,
  );
  return { de: chaveDoDia(domingo), ate: chaveDoDia(sabado) };
}

function atualizarTela() {
  mostrarIndicadores();
  mostrarProgresso();
  mostrarAssuntos();
  mostrarResumoDoDia();
  mostrarSugestoesDeCategoria();
  mostrarCalendario();
  mostrarContadores();
  mostrarLista();
}

async function carregarTarefas() {
  const botao = document.getElementById("tentar-novamente");
  botao.hidden = true;
  mostrarAviso("Carregando tarefas...");
  const grade = janelaDaGrade();
  const semana = janelaDaSemana();
  try {
    const [avulsas, daGrade, daSemana] = await Promise.all([
      data.listar(),
      data.agenda(grade.de, grade.ate, true),
      data.agenda(semana.de, semana.ate),
    ]);
    tarefasCarregadas = avulsas;
    itensAgenda = daGrade;
    itensSemana = daSemana;
  } catch (erro) {
    mostrarAviso(
      "Não foi possível carregar as tarefas. Verifique se o servidor está rodando.",
      true,
    );
    botao.hidden = false;
    return;
  }
  atualizarTela();
}

async function executarEAtualizar(acao) {
  try {
    await acao();
  } catch (erro) {
    mostrarAviso(erro.message, true);
    return;
  }
  await carregarTarefas();
}

// ===== Lista de tarefas =====
const ICONE_CHECK =
  '<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 6.5l2.5 2.5 4.5-5"/></svg>';
const ICONE_EDITAR =
  '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 14l3-1 8-8-2-2-8 8z"/></svg>';
const ICONE_EXCLUIR =
  '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 4h10M6 4V2h4v2M5 4l.5 9h5L11 4"/></svg>';

function compararItens(a, b) {
  return (
    Number(a.concluida) - Number(b.concluida) ||
    (a.dia || "9999-99-99").localeCompare(b.dia || "9999-99-99") ||
    (a.hora || "99:99").localeCompare(b.hora || "99:99") ||
    a.id.localeCompare(b.id)
  );
}

// O que a lista mostra: o dia escolhido ou, sem dia escolhido, o mês do calendário
// (mais as tarefas sem dia).
function itensDoEscopo() {
  if (diaSelecionado) {
    return itensAgenda.filter((item) => item.dia === diaSelecionado);
  }
  const ano = mesExibido.getFullYear();
  const mes = mesExibido.getMonth();
  const primeiro = chaveDoDia(new Date(ano, mes, 1));
  const ultimo = chaveDoDia(new Date(ano, mes + 1, 0));
  return itensAgenda.filter(
    (item) => item.dia === null || (item.dia >= primeiro && item.dia <= ultimo),
  );
}

function mostrarContadores() {
  const { total, concluidas, pendentes } = calcularIndicadores(itensDoEscopo());
  document.getElementById("cont-todas").textContent = total;
  document.getElementById("cont-pendentes").textContent = pendentes;
  document.getElementById("cont-concluidas").textContent = concluidas;
}

async function alternarConclusao(item) {
  await executarEAtualizar(() =>
    item.tipo === "tarefa"
      ? data.atualizar(item.tarefa_id, { concluida: !item.concluida })
      : data.salvarOcorrencia(item.recorrencia_id, item.data_original, {
          status: item.concluida ? "pendente" : "concluida",
        }),
  );
}

function perguntarEscopo(titulo, texto) {
  const dialogo = document.getElementById("dialogo-escopo");
  document.getElementById("escopo-titulo").textContent = titulo;
  document.getElementById("escopo-texto").textContent = texto;
  return new Promise((resolver) => {
    let escolha = null;
    const escolher = (valor) => () => {
      escolha = valor;
      dialogo.close();
    };
    document.getElementById("escopo-esta").onclick = escolher("esta");
    document.getElementById("escopo-seguintes").onclick = escolher("seguintes");
    document.getElementById("escopo-todas").onclick = escolher("todas");
    document.getElementById("escopo-cancelar").onclick = escolher(null);
    dialogo.addEventListener("close", () => resolver(escolha), { once: true });
    dialogo.showModal();
  });
}

async function editarItem(item) {
  if (item.tipo === "tarefa") {
    abrirDialogo("editar-tarefa", item);
    return;
  }
  const escopo = await perguntarEscopo(
    "Editar tarefa recorrente",
    `"${item.titulo}" se repete. Alterar só a ocorrência de ${rotuloDoDia(item.dia)}, esta e as próximas, ou todas?`,
  );
  if (escopo === "esta") {
    abrirDialogo("editar-ocorrencia", item);
  } else if (escopo === "todas" || escopo === "seguintes") {
    try {
      const regra = await data.buscarRecorrencia(item.recorrencia_id);
      abrirDialogo(
        escopo === "todas" ? "editar-regra" : "editar-seguintes",
        item,
        regra,
      );
    } catch (erro) {
      mostrarAviso(erro.message, true);
    }
  }
}

async function excluirItem(item) {
  if (item.tipo === "tarefa") {
    if (
      !window.confirm(
        `Excluir a tarefa "${item.titulo}"? Essa ação não pode ser desfeita.`,
      )
    ) {
      return;
    }
    await executarEAtualizar(() => data.excluir(item.tarefa_id));
    return;
  }
  const escopo = await perguntarEscopo(
    "Excluir tarefa recorrente",
    `"${item.titulo}" se repete. Excluir só a ocorrência de ${rotuloDoDia(item.dia)}, esta e as próximas, ou todas?`,
  );
  if (escopo === "esta") {
    await executarEAtualizar(() =>
      data.salvarOcorrencia(item.recorrencia_id, item.data_original, {
        status: "cancelada",
      }),
    );
  } else if (escopo === "seguintes") {
    const aviso = `Excluir ${rotuloDoDia(item.dia)} e as próximas ocorrências de "${item.titulo}"? Essa ação não pode ser desfeita.`;
    if (!window.confirm(aviso)) {
      return;
    }
    await executarEAtualizar(() =>
      data.excluirASeguir(item.recorrencia_id, item.data_original),
    );
  } else if (escopo === "todas") {
    if (
      !window.confirm(
        `Excluir todas as ocorrências de "${item.titulo}"? Essa ação não pode ser desfeita.`,
      )
    ) {
      return;
    }
    await executarEAtualizar(() =>
      data.excluirRecorrencia(item.recorrencia_id),
    );
  }
}

function criarBotaoAcao(rotulo, icone, aoClicar, classeExtra = "") {
  const botao = document.createElement("button");
  botao.type = "button";
  botao.className = `acao-item ${classeExtra}`.trim();
  botao.setAttribute("aria-label", rotulo);
  botao.title = rotulo;
  botao.innerHTML = icone;
  botao.addEventListener("click", aoClicar);
  return botao;
}

function criarMeta(item) {
  const meta = criarElemento("div", "meta");
  if (item.dia) {
    let texto = rotuloDoDia(item.dia);
    if (item.hora) {
      texto += ` • ${item.hora.slice(0, 5)}`;
    }
    if (item.duracao_min) {
      texto += ` (${formatarDuracao(item.duracao_min)})`;
    }
    meta.appendChild(criarElemento("span", "tag-item tag-dia", texto));
  }
  if (item.tipo === "recorrente") {
    meta.appendChild(criarElemento("span", "tag-item tag-repete", "↻ Repete"));
  }
  if (item.remarcada) {
    meta.appendChild(
      criarElemento("span", "tag-item tag-remarcada", "Remarcada"),
    );
  }
  if (item.categoria) {
    meta.appendChild(
      criarElemento("span", "tag-item tag-categoria", item.categoria),
    );
  }
  if (item.prioridade) {
    meta.appendChild(
      criarElemento(
        "span",
        `tag-item prioridade-${item.prioridade}`,
        ROTULOS_DE_PRIORIDADE[item.prioridade] || item.prioridade,
      ),
    );
  }
  return meta;
}

function criarItem(item) {
  const linha = document.createElement("li");
  linha.className = item.concluida ? "item concluida" : "item";

  const marca = document.createElement("button");
  marca.type = "button";
  marca.className = "marca";
  marca.setAttribute(
    "aria-label",
    item.concluida ? `Reabrir: ${item.titulo}` : `Concluir: ${item.titulo}`,
  );
  if (item.concluida) {
    marca.innerHTML = ICONE_CHECK;
  }
  marca.addEventListener("click", () => alternarConclusao(item));

  const corpo = criarElemento("div", "corpo-item");
  corpo.appendChild(criarElemento("strong", "titulo", item.titulo));
  if (item.descricao) {
    corpo.appendChild(criarElemento("small", "descricao", item.descricao));
  }
  const meta = criarMeta(item);
  if (meta.children.length > 0) {
    corpo.appendChild(meta);
  }

  const acoes = criarElemento("div", "acoes-item");
  acoes.append(
    criarBotaoAcao(`Editar: ${item.titulo}`, ICONE_EDITAR, () =>
      editarItem(item),
    ),
    criarBotaoAcao(
      `Excluir: ${item.titulo}`,
      ICONE_EXCLUIR,
      () => excluirItem(item),
      "perigo",
    ),
  );

  linha.append(marca, corpo, acoes);
  return linha;
}

function mostrarLista() {
  const termo = normalizar(termoBusca.trim());
  const base = itensDoEscopo();
  const visiveis = base.filter((item) => {
    if (filtroAtual === "pendentes" && item.concluida) return false;
    if (filtroAtual === "concluidas" && !item.concluida) return false;
    if (!termo) return true;
    return normalizar(
      `${item.titulo} ${item.descricao || ""} ${item.categoria || ""}`,
    ).includes(termo);
  });
  const ordenados = [...visiveis].sort(compararItens);
  document.getElementById("lista").replaceChildren(...ordenados.map(criarItem));

  if (ordenados.length > 0) {
    mostrarAviso("");
  } else if (tarefasCarregadas.length === 0 && itensAgenda.length === 0) {
    mostrarAviso("Nenhuma tarefa cadastrada ainda.");
  } else if (base.length === 0) {
    mostrarAviso(
      diaSelecionado
        ? "Nenhuma tarefa neste dia."
        : "Nenhuma tarefa neste mês.",
    );
  } else {
    mostrarAviso("Nenhuma tarefa encontrada com esse filtro ou busca.");
  }
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

// ===== Janela de nova tarefa e de edição =====
function mostrarSugestoesDeCategoria() {
  const vistas = new Map();
  [...tarefasCarregadas, ...itensAgenda].forEach((item) => {
    if (item.categoria && !vistas.has(normalizar(item.categoria))) {
      vistas.set(normalizar(item.categoria), item.categoria);
    }
  });
  const opcoes = [...vistas.values()].sort().map((nome) => {
    const opcao = document.createElement("option");
    opcao.value = nome;
    return opcao;
  });
  document.getElementById("categorias").replaceChildren(...opcoes);
}

function atualizarCamposDeRepeticao() {
  const frequencia = document.getElementById("campo-repete").value;
  const unidades = {
    diaria: "dia(s)",
    semanal: "semana(s)",
    mensal: "mês(es)",
  };
  document.getElementById("campos-repeticao").hidden = frequencia === "";
  document.getElementById("bloco-dias-semana").hidden =
    frequencia !== "semanal";
  document.getElementById("bloco-dia-mes").hidden = frequencia !== "mensal";
  document.getElementById("unidade-intervalo").textContent =
    unidades[frequencia] || "";
}

function abrirDialogo(modo = "nova", item = null, regra = null) {
  modoDoDialogo = modo;
  itemEmEdicao = item;
  document.getElementById("form-tarefa").reset();
  document.getElementById("erro-form").hidden = true;

  const titulos = {
    nova: "Nova tarefa",
    "editar-tarefa": "Editar tarefa",
    "editar-ocorrencia": "Editar esta ocorrência",
    "editar-regra": "Editar tarefa recorrente",
    "editar-seguintes": "Editar esta e as próximas",
  };
  const rotulosDoDia = {
    "editar-regra": "Início",
    "editar-seguintes": "A partir de",
    "editar-ocorrencia": "Dia (para remarcar)",
  };
  document.getElementById("titulo-dialogo").textContent = titulos[modo];
  document.getElementById("rotulo-dia").textContent =
    rotulosDoDia[modo] || "Dia";
  document.getElementById("dica-ocorrencia").hidden =
    modo !== "editar-ocorrencia";
  document.getElementById("bloco-repetir").hidden =
    modo === "editar-tarefa" || modo === "editar-ocorrencia";

  const fonte = regra || item;
  const preencher = (id, valor) => {
    document.getElementById(id).value = valor ?? "";
  };
  preencher("campo-titulo", fonte ? fonte.titulo : "");
  preencher("campo-descricao", fonte ? fonte.descricao : "");
  const diaDoCampo =
    modo === "editar-seguintes"
      ? item.data_original
      : regra
        ? regra.inicio
        : item
          ? item.dia
          : diaSelecionado;
  preencher("campo-dia", diaDoCampo);
  preencher("campo-hora", fonte && fonte.hora ? fonte.hora.slice(0, 5) : "");
  preencher("campo-duracao", fonte ? fonte.duracao_min : "");
  preencher("campo-prioridade", fonte ? fonte.prioridade : "");
  preencher("campo-categoria", fonte ? fonte.categoria : "");

  preencher("campo-repete", regra ? regra.frequencia : "");
  preencher("campo-intervalo", regra ? regra.intervalo : 1);
  preencher("campo-dia-mes", regra ? regra.dia_do_mes : "");
  preencher("campo-fim", regra ? regra.fim : "");
  const marcados = regra ? regra.dias_semana : [];
  document.querySelectorAll('input[name="dia-semana"]').forEach((caixa) => {
    caixa.checked = marcados.includes(Number(caixa.value));
  });
  atualizarCamposDeRepeticao();

  document.getElementById("dialogo-tarefa").showModal();
  document.getElementById("campo-titulo").focus();
}

function lerFormulario() {
  const texto = (id) => document.getElementById(id).value.trim();
  const numero = (id) => (texto(id) ? Number(texto(id)) : null);
  return {
    titulo: document.getElementById("campo-titulo").value,
    descricao: texto("campo-descricao") || null,
    dia: texto("campo-dia") || null,
    hora: texto("campo-hora") || null,
    duracao_min: numero("campo-duracao"),
    prioridade: texto("campo-prioridade") || null,
    categoria: texto("campo-categoria") || null,
    frequencia: texto("campo-repete") || null,
    intervalo: numero("campo-intervalo") || 1,
    dias_semana: [
      ...document.querySelectorAll('input[name="dia-semana"]:checked'),
    ].map((caixa) => Number(caixa.value)),
    dia_do_mes: numero("campo-dia-mes"),
    fim: texto("campo-fim") || null,
  };
}

function validarFormulario(campos) {
  const ocorrencia = modoDoDialogo === "editar-ocorrencia";
  const emSerie =
    modoDoDialogo === "editar-regra" || modoDoDialogo === "editar-seguintes";
  const repetivel = modoDoDialogo === "nova" || emSerie;
  if (!ocorrencia && campos.hora && !campos.dia) {
    return "Informe o dia junto com a hora.";
  }
  if (!ocorrencia && campos.duracao_min && !campos.hora) {
    return "Informe a hora de início para usar a duração.";
  }
  if (emSerie && !campos.frequencia) {
    return "Uma tarefa recorrente precisa de uma repetição. Para encerrar, defina um término ou exclua.";
  }
  if (
    modoDoDialogo === "editar-seguintes" &&
    campos.dia &&
    campos.dia < itemEmEdicao.data_original
  ) {
    return "A nova série não pode começar antes desta ocorrência.";
  }
  if (repetivel && campos.frequencia) {
    if (!campos.dia) {
      return "Informe o dia de início da repetição.";
    }
    if (campos.fim && campos.fim < campos.dia) {
      return "O término não pode ser antes do início.";
    }
  }
  return "";
}

function camposDaTarefa(campos) {
  return {
    titulo: campos.titulo,
    descricao: campos.descricao,
    dia: campos.dia,
    hora: campos.hora,
    duracao_min: campos.duracao_min,
    prioridade: campos.prioridade,
    categoria: campos.categoria,
  };
}

function camposDaRecorrencia(campos) {
  return {
    titulo: campos.titulo,
    descricao: campos.descricao,
    categoria: campos.categoria,
    prioridade: campos.prioridade,
    hora: campos.hora,
    duracao_min: campos.duracao_min,
    frequencia: campos.frequencia,
    intervalo: campos.intervalo,
    dias_semana:
      campos.frequencia === "semanal" && campos.dias_semana.length
        ? campos.dias_semana
        : null,
    dia_do_mes: campos.frequencia === "mensal" ? campos.dia_do_mes : null,
    inicio: campos.dia,
    fim: campos.fim,
  };
}

// Só o que mudou em relação ao que a ocorrência mostrava. Campo esvaziado (null)
// volta ao valor da regra.
function diferencasDaOcorrencia(item, campos) {
  const horaAtual = item.hora ? item.hora.slice(0, 5) : null;
  const comparacoes = {
    titulo: [campos.titulo.trim(), item.titulo],
    descricao: [campos.descricao, item.descricao || null],
    hora: [campos.hora, horaAtual],
    duracao_min: [campos.duracao_min, item.duracao_min],
    prioridade: [campos.prioridade, item.prioridade],
    categoria: [campos.categoria, item.categoria],
  };
  const mudancas = {};
  Object.entries(comparacoes).forEach(([nome, [novo, atual]]) => {
    if (novo !== atual) {
      mudancas[nome] = novo;
    }
  });
  if (campos.dia && campos.dia !== item.dia) {
    mudancas.dia = campos.dia;
  }
  return mudancas;
}

async function salvarFormulario(campos) {
  if (modoDoDialogo === "editar-tarefa") {
    return data.atualizar(itemEmEdicao.tarefa_id, camposDaTarefa(campos));
  }
  if (modoDoDialogo === "editar-ocorrencia") {
    const mudancas = diferencasDaOcorrencia(itemEmEdicao, campos);
    if (Object.keys(mudancas).length === 0) {
      return null;
    }
    return data.salvarOcorrencia(
      itemEmEdicao.recorrencia_id,
      itemEmEdicao.data_original,
      mudancas,
    );
  }
  if (modoDoDialogo === "editar-seguintes") {
    return data.alterarASeguir(
      itemEmEdicao.recorrencia_id,
      itemEmEdicao.data_original,
      camposDaRecorrencia(campos),
    );
  }
  if (modoDoDialogo === "editar-regra") {
    return data.atualizarRecorrencia(
      itemEmEdicao.recorrencia_id,
      camposDaRecorrencia(campos),
    );
  }
  if (campos.frequencia) {
    return data.criarRecorrencia(camposDaRecorrencia(campos));
  }
  return data.criar(camposDaTarefa(campos));
}

function configurarDialogoDeTarefa() {
  const dialogo = document.getElementById("dialogo-tarefa");
  const erro = document.getElementById("erro-form");

  document
    .getElementById("nova-tarefa")
    .addEventListener("click", () => abrirDialogo("nova"));
  document
    .getElementById("cancelar-tarefa")
    .addEventListener("click", () => dialogo.close());
  document
    .getElementById("campo-repete")
    .addEventListener("change", atualizarCamposDeRepeticao);

  document
    .getElementById("form-tarefa")
    .addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const campos = lerFormulario();
      const problema = validarFormulario(campos);
      if (problema) {
        erro.textContent = problema;
        erro.hidden = false;
        return;
      }
      try {
        await salvarFormulario(campos);
      } catch (falha) {
        erro.textContent = falha.message;
        erro.hidden = false;
        return;
      }
      dialogo.close();
      await carregarTarefas();
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

function atualizarChipDoDia() {
  const botao = document.getElementById("limpar-dia");
  botao.hidden = !diaSelecionado;
  if (diaSelecionado) {
    botao.textContent = `${rotuloDoDia(diaSelecionado)} ✕`;
  }
}

function selecionarDia(chave) {
  diaSelecionado = diaSelecionado === chave ? null : chave;
  atualizarChipDoDia();
  mostrarCalendario();
  mostrarProgresso();
  mostrarAssuntos();
  mostrarResumoDoDia();
  mostrarContadores();
  mostrarLista();
}

function mostrarCalendario() {
  const ano = mesExibido.getFullYear();
  const mes = mesExibido.getMonth();
  document.getElementById("titulo-mes").textContent =
    `${MESES_COMPLETOS[mes]} de ${ano}`;

  const contagemPorDia = {};
  itensAgenda.forEach((item) => {
    if (item.dia) {
      contagemPorDia[item.dia] = (contagemPorDia[item.dia] || 0) + 1;
    }
  });

  const celulas = INICIAIS_DIAS.map((letra) =>
    criarElemento("span", "dia-semana", letra),
  );
  const hoje = chaveDoDia(new Date());
  const deslocamento = new Date(ano, mes, 1).getDay();
  for (let i = 0; i < 42; i++) {
    const dia = new Date(ano, mes, 1 - deslocamento + i);
    const chave = chaveDoDia(dia);
    const celula = criarElemento("button", "dia", String(dia.getDate()));
    celula.type = "button";
    celula.setAttribute(
      "aria-label",
      `${dia.getDate()} de ${MESES_COMPLETOS[dia.getMonth()]}`,
    );
    celula.setAttribute("aria-pressed", String(chave === diaSelecionado));
    if (dia.getMonth() !== mes) celula.classList.add("fora");
    if (chave === hoje) celula.classList.add("hoje");
    if (contagemPorDia[chave]) celula.classList.add("com-tarefas");
    if (chave === diaSelecionado) celula.classList.add("selecionado");
    celula.addEventListener("click", () => selecionarDia(chave));
    celulas.push(celula);
  }
  document.getElementById("grade").replaceChildren(...celulas);
}

async function mudarMes(delta) {
  mesExibido = new Date(
    mesExibido.getFullYear(),
    mesExibido.getMonth() + delta,
    1,
  );
  diaSelecionado = null;
  atualizarChipDoDia();
  await carregarTarefas();
}

// ===== Início =====
async function iniciar() {
  aplicarTema(lerTemaSalvo());
  document.getElementById("botao-tema").addEventListener("click", alternarTema);

  atualizarRelogio();
  setInterval(atualizarRelogio, 15000);
  configurarAtalhoDeBusca();
  configurarFiltros();
  configurarDialogoDeTarefa();

  mostrarCalendario();
  document
    .getElementById("mes-anterior")
    .addEventListener("click", () => mudarMes(-1));
  document
    .getElementById("mes-seguinte")
    .addEventListener("click", () => mudarMes(1));
  document.getElementById("limpar-dia").addEventListener("click", () => {
    selecionarDia(diaSelecionado);
  });

  document.getElementById("busca").addEventListener("input", (evento) => {
    termoBusca = evento.target.value;
    mostrarLista();
  });
  document
    .getElementById("tentar-novamente")
    .addEventListener("click", carregarTarefas);

  await carregarTarefas();
}

iniciar();
