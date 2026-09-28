// Compartilhar: menu nativo do celular quando existe; senão, segue o link do WhatsApp.
(function () {
  "use strict";

  document.querySelectorAll("[data-compartilhar]").forEach(function (link) {
    if (!navigator.share) return;
    link.addEventListener("click", function (e) {
      e.preventDefault();
      navigator
        .share({ title: link.dataset.titulo, url: location.href })
        .catch(function () {}); // o eleitor fechou o menu
    });
  });
})();
