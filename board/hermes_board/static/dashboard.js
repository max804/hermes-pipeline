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

  // --- Größen-Resizer der Hauptbereiche -------------------------------------
  // Sidebar-Breite (--sidebar-w am .app-shell) und Board-Höhe (--board-h an
  // der .board-viewport) per Ziehgriff. Werte überleben den Reload via
  // localStorage; Doppelklick auf den Griff setzt den Bereich zurück.
  const shell = document.querySelector(".app-shell");
  const viewport = document.querySelector(".board-viewport");
  if (shell) {
    const gwBreite = localStorage.getItem("hermes-sidebar-w");
    if (gwBreite) shell.style.setProperty("--sidebar-w", gwBreite);
    const gwHoehe = localStorage.getItem("hermes-board-h");
    if (gwHoehe && viewport) viewport.style.setProperty("--board-h", gwHoehe);

    let aktiv = null, startX = 0, startY = 0, startW = 0, startH = 0;
    const sidebar = shell.querySelector(".sidebar");

    document.addEventListener("mousedown", (e) => {
      const griff = e.target.closest("[data-resize]");
      if (!griff) return;
      aktiv = griff.dataset.resize;
      startX = e.clientX; startY = e.clientY;
      startW = sidebar ? sidebar.offsetWidth : 200;
      startH = viewport ? viewport.offsetHeight : 0;
      griff.classList.add("aktiv");
      document.body.style.userSelect = "none";
      document.body.style.cursor = aktiv === "sidebar" ? "col-resize" : "row-resize";
      e.preventDefault();
    });
    document.addEventListener("mousemove", (e) => {
      if (!aktiv) return;
      if (aktiv === "sidebar") {
        const w = Math.min(440, Math.max(120, startW + (e.clientX - startX)));
        shell.style.setProperty("--sidebar-w", w + "px");
      } else if (aktiv === "board" && viewport) {
        const h = Math.max(160, startH + (e.clientY - startY));
        viewport.style.setProperty("--board-h", h + "px");
      }
    });
    document.addEventListener("mouseup", () => {
      if (!aktiv) return;
      if (aktiv === "sidebar") {
        localStorage.setItem("hermes-sidebar-w",
          shell.style.getPropertyValue("--sidebar-w").trim());
      } else if (aktiv === "board" && viewport) {
        localStorage.setItem("hermes-board-h",
          viewport.style.getPropertyValue("--board-h").trim());
      }
      document.querySelectorAll("[data-resize].aktiv")
        .forEach((el) => el.classList.remove("aktiv"));
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
      aktiv = null;
    });
    document.addEventListener("dblclick", (e) => {
      const griff = e.target.closest("[data-resize]");
      if (!griff) return;
      if (griff.dataset.resize === "sidebar") {
        shell.style.removeProperty("--sidebar-w");
        localStorage.removeItem("hermes-sidebar-w");
      } else if (viewport) {
        viewport.style.removeProperty("--board-h");
        localStorage.removeItem("hermes-board-h");
      }
    });
  }
})();
