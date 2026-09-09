function showTab(id) {
  document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".nav button").forEach((b) => b.classList.remove("active"));
  const panel = document.getElementById(id);
  if (panel) panel.classList.add("active");
  const btn = document.querySelector(`.nav button[data-tab="${id}"]`);
  if (btn) btn.classList.add("active");
}

document.querySelectorAll(".nav button").forEach((btn) => {
  btn.addEventListener("click", () => showTab(btn.dataset.tab));
});

const energy = document.getElementById("energy");
const energyVal = document.getElementById("energyVal");
if (energy && energyVal) {
  energy.addEventListener("input", () => {
    energyVal.textContent = energy.value;
  });
}

const params = new URLSearchParams(window.location.search);
const tab = params.get("tab");
if (tab) showTab(tab);

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/sw.js").catch(() => {});
  });
}