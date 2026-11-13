import { PIX_COPIA_COLA } from "./config.js";
import { mountDonation } from "./lib/donation.js";

function renderDonation() {
  const root = document.getElementById("donationRoot");
  if (!root) return;
  mountDonation(root, { payload: PIX_COPIA_COLA });
}

renderDonation();

window.addEventListener("pageshow", (event) => {
  if (event.persisted) renderDonation();
});
