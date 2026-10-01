// Usado pelos testes: lê um cartão (JSON) na entrada padrão e escreve o PDF na saída.
const ColinhaPDF = require("../../src/colinha/static/js/pdf-colinha.js");

let entrada = "";
process.stdin.on("data", (parte) => (entrada += parte));
process.stdin.on("end", () => {
  process.stdout.write(Buffer.from(ColinhaPDF.gerar(JSON.parse(entrada)), "latin1"));
});
