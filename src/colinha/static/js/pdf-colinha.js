// Colinha de bolso em PDF (change add-colinha-bolso). Monta o arquivo à mão, no próprio
// navegador: uma folha A4 com um cartão de 63 x 88 mm no canto superior esquerdo, para
// recortar. Usa só a fonte padrão do PDF (Helvetica), sem biblioteca e
// sem nenhuma requisição. O arquivo sai todo em ASCII (acentos como \ooo).
(function (raiz) {
  "use strict";

  var MM = 72 / 25.4;
  var A4 = { largura: 595.28, altura: 841.89 };
  var CARTAO = { x: 10, y: 10, largura: 63, altura: 88, margem: 3 };
  var MIN_FONTE = 6;

  // Larguras (1/1000 de em) dos códigos WinAnsi 32 a 255, das métricas AFM Core 14 da
  // Adobe (Helvetica.afm e Helvetica-Bold.afm, Copyright (c) 1985, 1987, 1989, 1990, 1997
  // Adobe Systems Incorporated. All Rights Reserved. Helvetica is a trademark of
  // Linotype-Hell AG and/or its subsidiaries). Só as larguras foram copiadas.
  var REGULAR = [
    278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
    1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
    333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
    556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584, 556,
    556, 556, 222, 556, 333, 1000, 556, 556, 333, 1000, 667, 333, 1000, 556, 611, 556,
    556, 222, 222, 333, 333, 350, 556, 1000, 333, 1000, 500, 333, 944, 556, 500, 667,
    556, 333, 556, 556, 556, 556, 260, 556, 333, 737, 370, 556, 584, 556, 737, 333,
    400, 584, 333, 333, 333, 556, 537, 278, 333, 333, 365, 556, 834, 834, 834, 611,
    667, 667, 667, 667, 667, 667, 1000, 722, 667, 667, 667, 667, 278, 278, 278, 278,
    722, 722, 778, 778, 778, 778, 778, 584, 778, 722, 722, 722, 722, 667, 667, 611,
    556, 556, 556, 556, 556, 556, 889, 500, 556, 556, 556, 556, 278, 278, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 584, 611, 556, 556, 556, 556, 500, 556, 500
  ];
  var NEGRITO = [
    278, 333, 474, 556, 556, 889, 722, 238, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 333, 333, 584, 584, 584, 611,
    975, 722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 333, 278, 333, 584, 556,
    333, 556, 611, 556, 611, 556, 333, 611, 611, 278, 278, 556, 278, 889, 611, 611,
    611, 611, 389, 556, 333, 611, 556, 778, 556, 556, 500, 389, 280, 389, 584, 556,
    556, 556, 278, 556, 500, 1000, 556, 556, 333, 1000, 667, 333, 1000, 556, 611, 556,
    556, 278, 278, 500, 500, 350, 556, 1000, 333, 1000, 556, 333, 944, 556, 500, 667,
    556, 333, 556, 556, 556, 556, 280, 556, 333, 737, 370, 556, 584, 556, 737, 333,
    400, 584, 333, 333, 333, 611, 556, 278, 333, 333, 365, 556, 834, 834, 834, 611,
    722, 722, 722, 722, 722, 722, 1000, 722, 667, 667, 667, 667, 278, 278, 278, 278,
    722, 722, 778, 778, 778, 778, 778, 584, 778, 722, 722, 722, 722, 667, 667, 611,
    556, 556, 556, 556, 556, 556, 889, 556, 556, 556, 556, 556, 278, 278, 278, 278,
    611, 611, 611, 611, 611, 611, 611, 584, 611, 611, 611, 611, 611, 556, 611, 556
  ];

  // Caracteres de 0x80 a 0x9F na WinAnsi (cp1252).
  var CP1252 = {
    "€": 0x80, "‚": 0x82, "ƒ": 0x83, "„": 0x84, "…": 0x85, "†": 0x86, "‡": 0x87, "ˆ": 0x88,
    "‰": 0x89, "Š": 0x8a, "‹": 0x8b, "Œ": 0x8c, "Ž": 0x8e, "‘": 0x91, "’": 0x92, "“": 0x93,
    "”": 0x94, "•": 0x95, "–": 0x96, "—": 0x97, "˜": 0x98, "™": 0x99, "š": 0x9a, "›": 0x9b,
    "œ": 0x9c, "ž": 0x9e, "Ÿ": 0x9f,
  };

  function codigo(ch) {
    var c = ch.charCodeAt(0);
    if (ch.length === 1 && c >= 32 && c < 127) return c;
    if (ch.length === 1 && c > 0xa0 && c <= 0xff && c !== 0xad) return c;
    if (Object.prototype.hasOwnProperty.call(CP1252, ch)) return CP1252[ch];
    return null;
  }

  // Texto -> códigos WinAnsi. Fora da tabela: letra sem acento, senão "?".
  function paraWinAnsi(texto) {
    var codigos = [];
    Array.from(String(texto).replace(/[ \s]+/g, " ").replace(/­/g, "")).forEach(function (ch) {
      var c = codigo(ch);
      if (c === null) {
        var base = ch.normalize("NFD").replace(/[̀-ͯ]/g, "");
        c = base.length === 1 ? codigo(base) : null;
      }
      codigos.push(c === null ? 63 : c);
    });
    return codigos;
  }

  function largura(codigos, negrito, tamanho) {
    var tabela = negrito ? NEGRITO : REGULAR;
    var soma = 0;
    codigos.forEach(function (c) { soma += tabela[c - 32]; });
    return (soma * tamanho) / 1000;
  }

  function stringPdf(codigos) {
    var s = "(";
    codigos.forEach(function (c) {
      if (c === 40 || c === 41 || c === 92) s += "\\" + String.fromCharCode(c);
      else if (c < 127) s += String.fromCharCode(c);
      else s += "\\" + ("00" + c.toString(8)).slice(-3);
    });
    return s + ")";
  }

  // Coordenadas em mm a partir do canto superior esquerdo da folha.
  function px(mm) { return (mm * MM).toFixed(2); }
  function py(mm) { return (A4.altura - mm * MM).toFixed(2); }

  function Desenho() { this.ops = []; }
  Desenho.prototype.texto = function (x, y, codigos, fonte, tamanho) {
    this.ops.push("BT /" + fonte + " " + tamanho.toFixed(2) + " Tf " + px(x) + " " + py(y) + " Td " + stringPdf(codigos) + " Tj ET");
  };
  Desenho.prototype.retangulo = function (x, y, l, a, espessura, tracejado) {
    this.ops.push(
      espessura.toFixed(2) + " w " + (tracejado ? "[3 2] 0 d " : "[] 0 d ") +
      px(x) + " " + py(y + a) + " " + (l * MM).toFixed(2) + " " + (a * MM).toFixed(2) + " re S"
    );
  };
  Desenho.prototype.linha = function (x1, y1, x2, y2, cinza) {
    this.ops.push(cinza + " G 0.4 w [] 0 d " + px(x1) + " " + py(y1) + " m " + px(x2) + " " + py(y2) + " l S 0 G");
  };

  // Texto que cabe em `maximo` mm: encolhe até 6 pt e depois corta com "…".
  function ajustar(codigos, negrito, tamanho, maximo) {
    var t = tamanho;
    while (t > MIN_FONTE && largura(codigos, negrito, t) / MM > maximo) t -= 0.25;
    if (largura(codigos, negrito, t) / MM <= maximo) return { codigos: codigos, tamanho: t };
    var c = codigos.slice();
    while (c.length && largura(c.concat([0x85]), negrito, t) / MM > maximo) c.pop();
    return { codigos: c.concat([0x85]), tamanho: t };
  }

  // Nome de urna seguido do partido (ou do aviso), sem nunca cortar o que vem depois.
  function linhaNome(nome, sufixo, maximo) {
    var tamanho = 6.5;
    var fim = paraWinAnsi(" · " + sufixo);
    var nomeAjustado = ajustar(paraWinAnsi(nome), false, tamanho, maximo - largura(fim, false, tamanho) / MM);
    if (nomeAjustado.tamanho < tamanho) {
      tamanho = nomeAjustado.tamanho;
      nomeAjustado = ajustar(paraWinAnsi(nome), false, tamanho, maximo - largura(fim, false, tamanho) / MM);
    }
    return { codigos: nomeAjustado.codigos.concat(fim), tamanho: nomeAjustado.tamanho };
  }

  function desenharCartao(cartao) {
    var d = new Desenho();
    var x0 = CARTAO.x;
    var y0 = CARTAO.y;
    var m = CARTAO.margem;
    var util = CARTAO.largura - 2 * m;

    // Aviso de recorte acima do contorno (texto, e não símbolo: a fonte de símbolos padrão
    // do PDF não aparece em todos os leitores).
    d.texto(x0, y0 - 2.5, paraWinAnsi("Recorte na linha tracejada"), "F1", 6);
    d.retangulo(x0, y0, CARTAO.largura, CARTAO.altura, 0.6, true);

    var titulo = ajustar(paraWinAnsi(cartao.titulo), true, 9, util);
    d.texto(x0 + m, y0 + m + 3, titulo.codigos, "F2", titulo.tamanho);
    d.linha(x0 + m, y0 + m + 5, x0 + CARTAO.largura - m, y0 + m + 5, 0);

    var topo = y0 + m + 6;
    var rodape = 7;
    var disponivel = y0 + CARTAO.altura - rodape - topo;
    var altura = Math.min(disponivel / Math.max(cartao.vagas.length, 1), 16);
    var lado = Math.min(5.5, altura - 6);

    cartao.vagas.forEach(function (v, i) {
      var y = topo + i * altura;
      if (i > 0) d.linha(x0 + m, y, x0 + CARTAO.largura - m, y, 0.6);
      var rotulo = ajustar(paraWinAnsi(v.cargo), true, 6.5, util);
      d.texto(x0 + m, y + 2.5, rotulo.codigos, "F2", rotulo.tamanho);

      var digitos = v.numero ? String(v.numero).split("") : new Array(v.digitos + 1).join(" ").split("");
      var tamDigito = lado * MM * 0.75;
      digitos.forEach(function (dig, j) {
        var bx = x0 + m + j * (lado + 1);
        var by = y + 3.1;
        d.retangulo(bx, by, lado, lado, 0.8, false);
        if (dig !== " ") {
          var cod = paraWinAnsi(dig);
          var l = largura(cod, true, tamDigito) / MM;
          d.texto(bx + (lado - l) / 2, by + lado / 2 + tamDigito * 0.36 / MM, cod, "F2", tamDigito);
        }
      });

      if (v.numero) {
        var nome = linhaNome(v.nome || "", v.aviso || v.partido || "", util);
        d.texto(x0 + m, y + 3.1 + lado + 2.2, nome.codigos, "F1", nome.tamanho);
      }
    });

    var yr = y0 + CARTAO.altura - rodape;
    d.linha(x0 + m, yr, x0 + CARTAO.largura - m, yr, 0);
    (cartao.rodape || []).slice(0, 2).forEach(function (texto, i) {
      var r = ajustar(paraWinAnsi(texto), false, 6, util);
      d.texto(x0 + m, yr + 2.6 + i * 2.6, r.codigos, "F1", r.tamanho);
    });
    return d.ops.join("\n");
  }

  // Arquivo PDF 1.4 completo, como string ASCII (um caractere por byte).
  function gerar(cartao) {
    var conteudo = desenharCartao(cartao);
    var objetos = [
      "<< /Type /Catalog /Pages 2 0 R >>",
      "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
      "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 " + A4.largura + " " + A4.altura + "]" +
        " /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 4 0 R >>",
      "<< /Length " + conteudo.length + " >>\nstream\n" + conteudo + "\nendstream",
      "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
      "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
      "<< /Title " + stringPdf(paraWinAnsi(cartao.titulo)) + " /Producer (Colinha do Voto) >>",
    ];
    var pdf = "%PDF-1.4\n";
    var posicoes = [];
    objetos.forEach(function (o, i) {
      posicoes.push(pdf.length);
      pdf += (i + 1) + " 0 obj\n" + o + "\nendobj\n";
    });
    var xref = pdf.length;
    pdf += "xref\n0 " + (objetos.length + 1) + "\n0000000000 65535 f \n";
    posicoes.forEach(function (p) { pdf += ("000000000" + p).slice(-10) + " 00000 n \n"; });
    pdf += "trailer\n<< /Size " + (objetos.length + 1) + " /Root 1 0 R /Info 7 0 R >>\nstartxref\n" + xref + "\n%%EOF\n";
    return pdf;
  }

  var api = { gerar: gerar, paraWinAnsi: paraWinAnsi, largura: largura };
  if (typeof module === "object" && module.exports) module.exports = api;
  else raiz.ColinhaPDF = api;
})(this);
