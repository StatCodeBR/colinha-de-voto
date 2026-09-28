// Busca e filtros das listas por cargo. Sem JavaScript, a lista estática continua completa.
(function () {
  "use strict";

  var form = document.getElementById("filtros");
  var lista = document.getElementById("candidatos");
  if (!form || !lista) return;

  var linhas = Array.prototype.slice.call(lista.querySelectorAll(".candidato"));
  var campo = {
    texto: document.getElementById("f-texto"),
    genero: document.getElementById("f-genero"),
    partido: document.getElementById("f-partido"),
    historico: document.getElementById("f-historico"),
    reeleicao: document.getElementById("f-reeleicao"),
    inaptas: document.getElementById("f-inaptas"),
  };
  var contador = document.getElementById("contador");
  var vazio = document.getElementById("vazio");

  function normalizar(texto) {
    return texto.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
  }

  // Filtros ativos, na ordem em que sugerimos tirar quando nada é encontrado.
  function ativos() {
    var lista = [];
    if (campo.reeleicao.checked) lista.push("o filtro de eleitos para este cargo");
    if (campo.historico.value) lista.push("o filtro de histórico");
    if (campo.partido.value) lista.push("o filtro de partido");
    if (campo.genero.value) lista.push("o filtro de gênero");
    if (campo.texto.value.trim()) lista.push("a busca");
    return lista;
  }

  function atualizar() {
    var termos = normalizar(campo.texto.value).split(/\s+/).filter(Boolean);
    var mostrarInaptas = campo.inaptas.checked;
    var total = 0;
    lista.classList.toggle("com-inaptas", mostrarInaptas);
    linhas.forEach(function (li) {
      var d = li.dataset;
      var ok =
        (mostrarInaptas || d.apto === "sim") &&
        (!campo.genero.value || d.genero === campo.genero.value) &&
        (!campo.partido.value || d.partido === campo.partido.value) &&
        (!campo.historico.value || d.historico === campo.historico.value) &&
        (!campo.reeleicao.checked || d.reeleicao === "sim") &&
        termos.every(function (t) { return d.busca.indexOf(t) !== -1; });
      li.hidden = !ok;
      if (ok) total += 1;
    });
    contador.textContent =
      total === 1 ? "1 candidatura encontrada" : total + " candidaturas encontradas";
    var filtros = ativos();
    if (total === 0) {
      vazio.textContent =
        "Nenhuma candidatura com esses filtros." +
        (filtros.length ? " Tente tirar " + filtros[0] + "." : "");
      vazio.hidden = false;
    } else {
      vazio.hidden = true;
    }
  }

  form.addEventListener("input", atualizar);
  form.addEventListener("change", atualizar);
  form.addEventListener("submit", function (e) { e.preventDefault(); });
  form.hidden = false;
  atualizar();
})();
