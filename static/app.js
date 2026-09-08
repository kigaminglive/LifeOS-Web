// Tab switching
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));

    btn.classList.add("active");
    const panel = document.getElementById(btn.dataset.tab);
    if (panel) {
      panel.classList.add("active");
    }
  });
});

// Energy slider live label
const energy = document.getElementById("energy");
const energyVal = document.getElementById("energyVal");

if (energy && energyVal) {
  energy.addEventListener("input", () => {
    energyVal.textContent = energy.value;
  });
}

// PWA service worker
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/sw.js").catch((err) => {
      console.log("SW failed", err);
    });
  });
}