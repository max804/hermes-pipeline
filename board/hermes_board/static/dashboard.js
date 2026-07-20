// Theme-Toggle (Dark ist Standard) und Client-Suche über Kartentitel.
// Beide überleben den HTMX-Swap des Kanban-Fensters.

(function () {
  const wurzel = document.documentElement;

  // Theme aus localStorage anwenden (Standard: dark = kein Attribut nötig)
  const gespeichert = localStorage.getItem("hermes-theme");
  if (gespeichert === "light") wurzel.setAttribute("data-theme", "light");

  document.addEventListener("click", (e) => {
    if (!e.target.closest("[data-action='theme']")) return;
    const hell = wurzel.getAttribute("data-theme") === "light";
    if (hell) {
      wurzel.removeAttribute("data-theme");
      localStorage.setItem("hermes-theme", "dark");
    } else {
      wurzel.setAttribute("data-theme", "light");
      localStorage.setItem("hermes-theme", "light");
    }
  });

  // Client-Suche: blendet Karten aus, deren Titel/ID nicht passen
  function filterAnwenden() {
    const feld = document.querySelector("#kartensuche");
    if (!feld) return;
    const suchwort = feld.value.trim().toLowerCase();
    document.querySelectorAll(".task-card").forEach((karte) => {
      const text = karte.textContent.toLowerCase();
      karte.style.display = !suchwort || text.includes(suchwort) ? "" : "none";
    });
  }
  document.addEventListener("input", (e) => {
    if (e.target.id === "kartensuche") filterAnwenden();
  });
  document.body.addEventListener("htmx:afterSwap", filterAnwenden);
})();
