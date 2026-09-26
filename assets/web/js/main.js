/* ==========================================================================
   Primordial · Mejoras progresivas de la web oficial
   Sin dependencias externas. Todo es opcional: si JS falla, la página
   sigue siendo completamente legible (mejora progresiva).
   ========================================================================== */
(function () {
  "use strict";

  // Marca que hay JS disponible: las animaciones solo se aplican con esta clase
  document.documentElement.classList.add("js");

  // Año dinámico en el pie
  var year = document.getElementById("year");
  if (year) {
    year.textContent = String(new Date().getFullYear());
  }

  // Aparición suave de secciones al hacer scroll
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduceMotion || !("IntersectionObserver" in window)) {
    return;
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll("main section").forEach(function (el) {
    observer.observe(el);
  });
})();