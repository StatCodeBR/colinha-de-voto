// Colinha do eleitor. Fica só no localStorage deste navegador: nada é enviado a servidor.
// Chaves: "colinha:v1:{UF}" (escolhas por cargo) e "colinha:v1:BR" (presidente, vale para
// todas as UFs); "colinha:uf" guarda a última UF visitada.
(function () {
  "use strict";

  var PREFIXO = "colinha:v1:";
  var CHAVE_UF = "colinha:uf";
  var memoria = {};
  var semArmazenamento = false;

  function ler(chave) {
    if (!semArmazenamento) {
      try {
        var valor = localStorage.getItem(chave);
        return valor === null ? null : JSON.parse(valor);
      } catch (e) {
        semArmazenamento = true;
      }
    }
    return Object.prototype.hasOwnProperty.call(memoria, chave) ? memoria[chave] : null;
  }

  function gravar(chave, valor) {
    memoria[chave] = valor;
    if (semArmazenamento) return avisarSemArmazenamento();
    try {
      localStorage.setItem(chave, JSON.stringify(valor));
    } catch (e) {
      semArmazenamento = true;
      avisarSemArmazenamento();
    }
  }

  function remover(chave) {
    delete memoria[chave];
    try {
      localStorage.removeItem(chave);
    } catch (e) {}
  }

  function avisarSemArmazenamento() {
    var aviso = document.getElementById("colinha-aviso") || document.getElementById("aviso-armazenamento");
    if (!aviso) {
      aviso = document.createElement("p");
      aviso.id = "aviso-armazenamento";
      aviso.className = "aviso";
      aviso.setAttribute("role", "status");
      document.getElementById("conteudo").prepend(aviso);
    }
    aviso.textContent =
      "Este navegador não deixa guardar a colinha. Ela funciona enquanto esta página " +
      "estiver aberta; anote seus números antes de sair.";
    aviso.hidden = false;
  }

  function colinha(uf) {
    return ler(PREFIXO + uf) || {};
  }

  function escolhidos(uf, cargo) {
    return colinha(uf)[cargo] || [];
  }

  function salvar(uf, cargo, lista) {
    var c = colinha(uf);
    c[cargo] = lista;
    gravar(PREFIXO + uf, c);
  }

  // --- Última UF visitada -------------------------------------------------------------

  var marcaUf = document.querySelector("[data-uf-atual]");
  if (marcaUf) {
    gravar(CHAVE_UF, {
      sigla: marcaUf.dataset.ufAtual,
      nome: marcaUf.dataset.ufNome,
      em: marcaUf.dataset.ufEm,
    });
  }

  var atalho = document.getElementById("atalho-uf");
  var ultima = ler(CHAVE_UF);
  if (atalho && ultima && ultima.sigla) {
    var link = document.createElement("a");
    link.href = "/" + ultima.sigla.toLowerCase() + "/";
    // "em" ausente: valor guardado por uma versão anterior do site.
    link.textContent = "Continuar " + (ultima.em || "em " + ultima.nome);
    atalho.appendChild(link);
    atalho.hidden = false;
  }

  // Páginas de presidente servem a todas as UFs: o "Voltar" leva à lista de presidente da
  // última UF visitada. Sem UF guardada, fica o destino do HTML (escolha de estado).
  var voltarPresidente = document.querySelector("[data-voltar-presidente]");
  if (voltarPresidente && ultima && ultima.sigla) {
    voltarPresidente.href = "/" + ultima.sigla.toLowerCase() + "/presidente/";
    voltarPresidente.lastChild.textContent = "Voltar para presidente";
  }

  // --- Botões "Adicionar à colinha" ----------------------------------------------------

  function candidatoDoBotao(b) {
    return { id: b.dataset.id, numero: b.dataset.numero, nome: b.dataset.nome, partido: b.dataset.partido, url: b.dataset.url };
  }

  function atualizarBotoes() {
    document.querySelectorAll("[data-colinha]").forEach(function (b) {
      var dentro = escolhidos(b.dataset.uf, b.dataset.cargo).some(function (c) {
        return c.id === b.dataset.id;
      });
      b.setAttribute("aria-pressed", dentro ? "true" : "false");
      b.textContent = dentro ? "Tirar da colinha" : "Adicionar à colinha";
      b.hidden = false;
    });
  }

  function alternar(b) {
    var uf = b.dataset.uf;
    var cargo = b.dataset.cargo;
    var vagas = parseInt(b.dataset.vagas, 10) || 1;
    var novo = candidatoDoBotao(b);
    var lista = escolhidos(uf, cargo);
    var jaEsta = lista.some(function (c) { return c.id === novo.id; });

    if (jaEsta) {
      salvar(uf, cargo, lista.filter(function (c) { return c.id !== novo.id; }));
    } else if (lista.length < vagas) {
      salvar(uf, cargo, lista.concat([novo]));
    } else {
      var antigo = lista[0];
      var pergunta =
        (vagas > 1
          ? "As " + vagas + " vagas de " + b.dataset.rotulo.toLowerCase() + " já estão preenchidas. "
          : "Sua colinha já tem " + antigo.nome + " (" + antigo.numero + ") para " + b.dataset.rotulo.toLowerCase() + ". ") +
        "Trocar " + antigo.nome + " por " + novo.nome + "?";
      if (!window.confirm(pergunta)) return;
      salvar(uf, cargo, lista.slice(1).concat([novo]));
    }
    atualizarBotoes();
  }

  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest("[data-colinha]");
    if (b) alternar(b);
  });
  atualizarBotoes();

  // --- Página /colinha/ ------------------------------------------------------------------

  var raiz = document.getElementById("colinha");
  if (!raiz) return;
  var config = JSON.parse(raiz.dataset.config);

  function el(tag, classe, texto) {
    var n = document.createElement(tag);
    if (classe) n.className = classe;
    if (texto !== undefined) n.textContent = texto;
    return n;
  }

  function numero(n) {
    var s = el("span", "numero");
    s.setAttribute("role", "img");
    s.setAttribute("aria-label", "número " + n);
    n.split("").forEach(function (d) {
      var dig = el("span", "digito", d);
      dig.setAttribute("aria-hidden", "true");
      s.appendChild(dig);
    });
    return s;
  }

  function slug(cargo) {
    return config.rotulos[cargo].toLowerCase().replace(/ /g, "-");
  }

  function escolherUf() {
    raiz.appendChild(el("p", null, "Escolha o estado em que você vota:"));
    var ul = el("ul", "lista-ufs");
    Object.keys(config.nomesUf).forEach(function (sigla) {
      var li = el("li");
      var a = el("a", null, config.nomesUf[sigla]);
      a.href = "?uf=" + sigla;
      li.appendChild(a);
      ul.appendChild(li);
    });
    raiz.appendChild(ul);
  }

  var params = new URLSearchParams(location.search);
  // "?uf=" vazio (link "Trocar de estado") abre a escolha mesmo com UF guardada.
  var uf = (params.has("uf") ? params.get("uf") : (ultima && ultima.sigla) || "").toUpperCase();
  if (!config.cargosPorUf[uf]) {
    escolherUf();
    return;
  }
  if (semArmazenamento) avisarSemArmazenamento();

  var titulo = el("h2", null, "Colinha " + config.deUf[uf]);
  raiz.appendChild(titulo);
  var trocar = el("a", null, "Trocar de estado");
  trocar.href = "?uf=";
  raiz.appendChild(el("p", "trocar-uf")).appendChild(trocar);

  var ol = el("ol", "vagas");
  var slots = [];
  config.cargosPorUf[uf].forEach(function (cargo) {
    var chave = cargo === "PRESIDENTE" ? "BR" : uf;
    var vagas = config.vagas[cargo];
    var lista = escolhidos(chave, cargo);
    for (var i = 0; i < vagas; i++) {
      var li = el("li", "vaga");
      var rotulo = config.rotulos[cargo] + (vagas > 1 ? ", " + (i + 1) + "º voto" : "");
      li.appendChild(el("span", "vaga-cargo", rotulo));
      var c = lista[i];
      if (c) {
        var escolha = el("span", "vaga-escolha");
        escolha.appendChild(numero(c.numero));
        var nome = el("a", null, c.nome);
        nome.href = c.url;
        escolha.appendChild(nome);
        escolha.appendChild(el("span", null, c.partido));
        li.appendChild(escolha);
        slots.push({ li: li, candidato: c, chave: chave });
      } else {
        var vazio = el("span", "vaga-vazia", "Ainda não escolhido. ");
        var ver = el("a", null, "Ver candidaturas");
        ver.href = "/" + uf.toLowerCase() + "/" + slug(cargo) + "/";
        vazio.appendChild(ver);
        li.appendChild(vazio);
      }
      ol.appendChild(li);
    }
  });
  raiz.appendChild(ol);

  var acoes = document.getElementById("colinha-acoes");
  acoes.hidden = false;
  document.getElementById("imprimir").addEventListener("click", function () {
    window.print();
  });
  document.getElementById("apagar").addEventListener("click", function () {
    if (!window.confirm("Apagar todas as escolhas da colinha " + config.deUf[uf] + ", inclusive a de presidente?")) return;
    remover(PREFIXO + uf);
    remover(PREFIXO + "BR");
    location.reload();
  });

  // Confere as escolhas guardadas contra os índices atuais (colinha desatualizada).
  function conferir(chave, indice) {
    var situacao = {};
    indice.candidatos.forEach(function (c) { situacao[c.id] = c.apto; });
    slots.forEach(function (s) {
      if (s.chave !== chave) return;
      var texto = null;
      if (!(s.candidato.id in situacao)) {
        texto = "Esta candidatura não aparece mais nos dados do TSE. Escolha outra.";
      } else if (!situacao[s.candidato.id]) {
        texto = "Esta candidatura não está mais apta. Veja a situação na página e considere escolher outra.";
      }
      if (texto) s.li.appendChild(el("span", "aviso-vaga", texto));
    });
  }

  [uf, "BR"].forEach(function (chave) {
    if (!slots.some(function (s) { return s.chave === chave; })) return;
    fetch("/dados/" + chave + ".json")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (indice) { if (indice) conferir(chave, indice); })
      .catch(function () {});
  });
})();
