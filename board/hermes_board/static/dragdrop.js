// Drag & Drop zwischen Spalten — Event-Delegation, überlebt HTMX-Swaps.
// Während des Ziehens pausiert das Board-Polling (window.hermesZieht,
// abgefragt in der hx-trigger-Bedingung von board.html).

document.addEventListener("dragstart", (e) => {
  const karte = e.target.closest("[data-karte]");
  if (!karte) return;
  window.hermesZieht = true;
  e.dataTransfer.setData("text/plain", karte.dataset.karte);
  e.dataTransfer.effectAllowed = "move";
});

document.addEventListener("dragend", () => {
  window.hermesZieht = false;
});

document.addEventListener("dragover", (e) => {
  if (e.target.closest("[data-spalte]")) {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  }
});

document.addEventListener("drop", async (e) => {
  const spalte = e.target.closest("[data-spalte]");
  const id = e.dataTransfer.getData("text/plain");
  if (!spalte || !id) return;
  e.preventDefault();
  window.hermesZieht = false;
  await fetch(`/api/karten/${id}/verschieben`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ spalte: spalte.dataset.spalte }),
  });
  document.body.dispatchEvent(new Event("board-refresh"));
});
