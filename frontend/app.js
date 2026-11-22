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

const data = {
  async listar() {
    const resposta = await fetch("/tarefas");
    if (!resposta.ok) {
      throw new Error("Falha ao listar as tarefas");
    }
    return resposta.json();
  },

  async criar(campos) {
    const resposta = await fetch("/tarefas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(campos),
    });
    if (!resposta.ok) {
      throw new Error(
        await mensagemDeErro(resposta, "Não foi possível cadastrar a tarefa."),
      );
    }
    return resposta.json();
  },

  async atualizar(id, campos) {
    const resposta = await fetch(`/tarefas/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(campos),
    });
    if (!resposta.ok) {
      throw new Error(
        await mensagemDeErro(resposta, "Não foi possível atualizar a tarefa."),
      );
    }
    return resposta.json();
  },

  async excluir(id) {
    const resposta = await fetch(`/tarefas/${id}`, { method: "DELETE" });
    if (!resposta.ok && resposta.status !== 404) {
      throw new Error("Não foi possível excluir a tarefa.");
    }
  },
};

// ===== Estado da tela =====
let tarefasCarregadas = [];
let filtroAtual = "todas";
let termoBusca = "";
let tarefaEmEdicao = null;
let diaSelecionado = null;
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

// ===== Indicadores e progresso: sempre calculados a partir da lista =====
function tarefasDaSemana(tarefas) {
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
  const de = chaveDoDia(domingo);
  const ate = chaveDoDia(sabado);
  return tarefas.filter(
    (tarefa) => tarefa.dia && tarefa.dia >= de && tarefa.dia <= ate,
  ).length;
}

function calcularIndicadores(tarefas) {
  const total = tarefas.length;
  const concluidas = tarefas.filter((tarefa) => tarefa.concluida).length;
  return {
    total,
    concluidas,
    pendentes: total - concluidas,
    semana: tarefasDaSemana(tarefas),
  };
}

function mostrarIndicadores(indicadores) {
  document.getElementById("kpi-total").textContent = indicadores.total;
  document.getElementById("kpi-concluidas").textContent =
    indicadores.concluidas;
  document.getElementById("kpi-pendentes").textContent = indicadores.pendentes;
  document.getElementById("kpi-semana").textContent = indicadores.semana;
}

function mostrarContadores() {
  const { total, concluidas, pendentes } =
    calcularIndicadores(tarefasCarregadas);
  document.getElementById("cont-todas").textContent = total;
  document.getElementById("cont-pendentes").textContent = pendentes;
  document.getElementById("cont-concluidas").textContent = concluidas;
}

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

// ===== Painel Sobre seus assuntos: categorias e resumo do dia =====
function mostrarAssuntos() {
  const alvo = document.getElementById("assuntos");
  const contagem = new Map();
  tarefasCarregadas.forEach((tarefa) => {
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
        "Por assunto: aparece quando você der uma categoria às tarefas.",
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

function mostrarResumoDoDia() {
  const alvo = document.getElementById("resumo-dia");
  const chave = diaSelecionado || chaveDoDia(new Date());
  const doDia = tarefasCarregadas.filter((tarefa) => tarefa.dia === chave);
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

  const concluidas = doDia.filter((tarefa) => tarefa.concluida).length;
  const minutos = doDia.reduce(
    (soma, tarefa) => soma + (tarefa.duracao_min || 0),
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

function atualizarTela() {
  mostrarIndicadores(calcularIndicadores(tarefasCarregadas));
  mostrarContadores();
  mostrarProgresso();
  mostrarAssuntos();
  mostrarResumoDoDia();
  mostrarSugestoesDeCategoria();
  mostrarCalendario();
  mostrarLista();
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
  atualizarTela();
}

// ===== Lista de tarefas =====
const ICONE_CHECK =
  '<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 6.5l2.5 2.5 4.5-5"/></svg>';
const ICONE_EDITAR =
  '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 14l3-1 8-8-2-2-8 8z"/></svg>';
const ICONE_EXCLUIR =
  '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 4h10M6 4V2h4v2M5 4l.5 9h5L11 4"/></svg>';

function compararTarefas(a, b) {
  return (
    Number(a.concluida) - Number(b.concluida) ||
    (a.dia || "9999-99-99").localeCompare(b.dia || "9999-99-99") ||
    (a.hora || "99:99").localeCompare(b.hora || "99:99") ||
    a.id - b.id
  );
}

async function alternarConclusao(tarefa) {
  try {
    await data.atualizar(tarefa.id, { concluida: !tarefa.concluida });
  } catch (erro) {
    mostrarAviso(erro.message, true);
    return;
  }
  await carregarTarefas();
}

async function excluirTarefa(tarefa) {
  if (
    !window.confirm(
      `Excluir a tarefa "${tarefa.titulo}"? Essa ação não pode ser desfeita.`,
    )
  ) {
    return;
  }
  try {
    await data.excluir(tarefa.id);
  } catch (erro) {
    mostrarAviso(erro.message, true);
    return;
  }
  await carregarTarefas();
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

function criarMeta(tarefa) {
  const meta = criarElemento("div", "meta");
  if (tarefa.dia) {
    let texto = rotuloDoDia(tarefa.dia);
    if (tarefa.hora) {
      texto += ` • ${tarefa.hora.slice(0, 5)}`;
    }
    if (tarefa.duracao_min) {
      texto += ` (${formatarDuracao(tarefa.duracao_min)})`;
    }
    meta.appendChild(criarElemento("span", "tag-item tag-dia", texto));
  }
  if (tarefa.categoria) {
    meta.appendChild(
      criarElemento("span", "tag-item tag-categoria", tarefa.categoria),
    );
  }
  if (tarefa.prioridade) {
    meta.appendChild(
      criarElemento(
        "span",
        `tag-item prioridade-${tarefa.prioridade}`,
        ROTULOS_DE_PRIORIDADE[tarefa.prioridade] || tarefa.prioridade,
      ),
    );
  }
  return meta;
}

function criarItem(tarefa) {
  const item = document.createElement("li");
  item.className = tarefa.concluida ? "item concluida" : "item";

  const marca = document.createElement("button");
  marca.type = "button";
  marca.className = "marca";
  marca.setAttribute(
    "aria-label",
    tarefa.concluida
      ? `Reabrir: ${tarefa.titulo}`
      : `Concluir: ${tarefa.titulo}`,
  );
  if (tarefa.concluida) {
    marca.innerHTML = ICONE_CHECK;
  }
  marca.addEventListener("click", () => alternarConclusao(tarefa));

  const corpo = criarElemento("div", "corpo-item");
  corpo.appendChild(criarElemento("strong", "titulo", tarefa.titulo));
  if (tarefa.descricao) {
    corpo.appendChild(criarElemento("small", "descricao", tarefa.descricao));
  }
  const meta = criarMeta(tarefa);
  if (meta.children.length > 0) {
    corpo.appendChild(meta);
  }

  const acoes = criarElemento("div", "acoes-item");
  acoes.append(
    criarBotaoAcao(`Editar: ${tarefa.titulo}`, ICONE_EDITAR, () =>
      abrirDialogo(tarefa),
    ),
    criarBotaoAcao(
      `Excluir: ${tarefa.titulo}`,
      ICONE_EXCLUIR,
      () => excluirTarefa(tarefa),
      "perigo",
    ),
  );

  item.append(marca, corpo, acoes);
  return item;
}

function mostrarLista() {
  const termo = normalizar(termoBusca.trim());
  const visiveis = tarefasCarregadas.filter((tarefa) => {
    if (filtroAtual === "pendentes" && tarefa.concluida) return false;
    if (filtroAtual === "concluidas" && !tarefa.concluida) return false;
    if (diaSelecionado && tarefa.dia !== diaSelecionado) return false;
    if (!termo) return true;
    return normalizar(
      `${tarefa.titulo} ${tarefa.descricao || ""} ${tarefa.categoria || ""}`,
    ).includes(termo);
  });
  const ordenadas = [...visiveis].sort(compararTarefas);
  document.getElementById("lista").replaceChildren(...ordenadas.map(criarItem));

  if (tarefasCarregadas.length === 0) {
    mostrarAviso("Nenhuma tarefa cadastrada ainda.");
  } else if (ordenadas.length === 0) {
    mostrarAviso(
      diaSelecionado && !termo && filtroAtual === "todas"
        ? "Nenhuma tarefa neste dia."
        : "Nenhuma tarefa encontrada com esse filtro, dia ou busca.",
    );
  } else {
    mostrarAviso("");
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
  tarefasCarregadas.forEach((tarefa) => {
    if (tarefa.categoria && !vistas.has(normalizar(tarefa.categoria))) {
      vistas.set(normalizar(tarefa.categoria), tarefa.categoria);
    }
  });
  const opcoes = [...vistas.values()].sort().map((nome) => {
    const opcao = document.createElement("option");
    opcao.value = nome;
    return opcao;
  });
  document.getElementById("categorias").replaceChildren(...opcoes);
}

function abrirDialogo(tarefa = null) {
  tarefaEmEdicao = tarefa;
  document.getElementById("form-tarefa").reset();
  document.getElementById("erro-form").hidden = true;
  document.getElementById("titulo-dialogo").textContent = tarefa
    ? "Editar tarefa"
    : "Nova tarefa";

  const preencher = (id, valor) => {
    document.getElementById(id).value = valor ?? "";
  };
  preencher("campo-titulo", tarefa ? tarefa.titulo : "");
  preencher("campo-descricao", tarefa ? tarefa.descricao : "");
  preencher("campo-dia", tarefa ? tarefa.dia : diaSelecionado);
  preencher("campo-hora", tarefa && tarefa.hora ? tarefa.hora.slice(0, 5) : "");
  preencher("campo-duracao", tarefa ? tarefa.duracao_min : "");
  preencher("campo-prioridade", tarefa ? tarefa.prioridade : "");
  preencher("campo-categoria", tarefa ? tarefa.categoria : "");

  document.getElementById("dialogo-tarefa").showModal();
  document.getElementById("campo-titulo").focus();
}

function lerFormulario() {
  const texto = (id) => document.getElementById(id).value.trim();
  const duracao = texto("campo-duracao");
  return {
    titulo: document.getElementById("campo-titulo").value,
    descricao: texto("campo-descricao") || null,
    dia: texto("campo-dia") || null,
    hora: texto("campo-hora") || null,
    duracao_min: duracao ? Number(duracao) : null,
    prioridade: texto("campo-prioridade") || null,
    categoria: texto("campo-categoria") || null,
  };
}

function validarFormulario(campos) {
  if (campos.hora && !campos.dia) {
    return "Informe o dia junto com a hora.";
  }
  if (campos.duracao_min && !campos.hora) {
    return "Informe a hora de início para usar a duração.";
  }
  return "";
}

function configurarDialogoDeTarefa() {
  const dialogo = document.getElementById("dialogo-tarefa");
  const erro = document.getElementById("erro-form");

  document
    .getElementById("nova-tarefa")
    .addEventListener("click", () => abrirDialogo());
  document
    .getElementById("cancelar-tarefa")
    .addEventListener("click", () => dialogo.close());

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
        if (tarefaEmEdicao) {
          await data.atualizar(tarefaEmEdicao.id, campos);
        } else {
          await data.criar(campos);
        }
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
  mostrarResumoDoDia();
  mostrarLista();
}

function mostrarCalendario() {
  const ano = mesExibido.getFullYear();
  const mes = mesExibido.getMonth();
  document.getElementById("titulo-mes").textContent =
    `${MESES_COMPLETOS[mes]} de ${ano}`;

  const contagemPorDia = {};
  tarefasCarregadas.forEach((tarefa) => {
    if (tarefa.dia) {
      contagemPorDia[tarefa.dia] = (contagemPorDia[tarefa.dia] || 0) + 1;
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

function mudarMes(delta) {
  mesExibido = new Date(
    mesExibido.getFullYear(),
    mesExibido.getMonth() + delta,
    1,
  );
  mostrarCalendario();
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
