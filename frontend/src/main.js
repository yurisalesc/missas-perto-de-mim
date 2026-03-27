const apiBase = "http://127.0.0.1:8000";
let currentCoords = null;

const map = L.map("map").setView([-5.7945, -35.211], 12);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

const markers = [];
const resultsList = document.getElementById("results");
const suggestionStatus = document.getElementById("suggestionStatus");
const allMassesList = document.getElementById("allMasses");

function clearResults() {
  markers.forEach((marker) => marker.remove());
  markers.length = 0;
  resultsList.innerHTML = "";
}

function renderResults(items) {
  clearResults();
  if (!Array.isArray(items) || items.length === 0) {
    const li = document.createElement("li");
    li.textContent =
      "Nenhuma missa encontrada na janela de tempo. Dica: aumente as horas, confira a cidade ou use sua localização.";
    resultsList.appendChild(li);
    return;
  }
  items.forEach((item) => {
    const marker = L.marker([item.latitude, item.longitude]).addTo(map);
    marker.bindPopup(`${item.nome}<br>${item.endereco}`);
    markers.push(marker);

    const li = document.createElement("li");
    const masses = item.proximas_missas
      .map((mass) => `${mass.dia_semana} - ${mass.horario.substring(0, 5)}`)
      .join(", ");
    li.textContent = `${item.nome} | ${item.endereco} | ${item.distancia_km} km | ${masses}`;
    resultsList.appendChild(li);
  });
}

async function runSearch() {
  const city = document.getElementById("city").value.trim();
  const radius = document.getElementById("radius").value;
  const hours = document.getElementById("hours").value;
  const params = new URLSearchParams();
  params.set("radius_km", radius);
  params.set("next_hours", hours);
  if (city) {
    params.set("city", city);
  }
  if (currentCoords) {
    params.set("lat", String(currentCoords.lat));
    params.set("lon", String(currentCoords.lon));
  }
  const response = await fetch(`${apiBase}/igrejas/buscar?${params.toString()}`);
  const payload = await response.json();
  renderResults(payload);
}

document.getElementById("geo").addEventListener("click", () => {
  if (!navigator.geolocation) {
    alert("Seu navegador não suporta geolocalização.");
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (position) => {
      currentCoords = {
        lat: position.coords.latitude,
        lon: position.coords.longitude,
      };
      map.setView([currentCoords.lat, currentCoords.lon], 13);
    },
    (error) => {
      alert(
        `Não foi possível obter sua localização (${error.code}). ` +
          "Dica: rode o site em http://localhost:5173 ou https e permita o acesso à localização."
      );
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
});

document.getElementById("search").addEventListener("click", runSearch);

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/src/sw.js");
}

document.getElementById("suggestionForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  suggestionStatus.textContent = "Enviando...";
  const payload = {
    nome_igreja: document.getElementById("sug_nome").value.trim(),
    endereco: document.getElementById("sug_endereco").value.trim(),
    cidade: document.getElementById("sug_cidade").value.trim(),
    mensagem: document.getElementById("sug_msg").value.trim() || null,
  };
  try {
    const response = await fetch(`${apiBase}/sugestoes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text);
    }
    suggestionStatus.textContent = "Sugestão enviada para moderação. Obrigado!";
    event.target.reset();
  } catch (e) {
    suggestionStatus.textContent = "Falha ao enviar sugestão. Tente novamente.";
  }
});

document.getElementById("listar_todas").addEventListener("click", async () => {
  allMassesList.innerHTML = "";
  const nomeIgreja = document.getElementById("filtro_igreja").value.trim();
  const params = new URLSearchParams();
  if (nomeIgreja) {
    params.set("nome_igreja", nomeIgreja);
  }
  const response = await fetch(`${apiBase}/missas/todas?${params.toString()}`);
  const payload = await response.json();
  if (!Array.isArray(payload) || payload.length === 0) {
    const li = document.createElement("li");
    li.textContent = "Nenhuma missa encontrada para esse filtro.";
    allMassesList.appendChild(li);
    return;
  }
  payload.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = `${item.nome_igreja} | Dia ${item.dia_semana} | ${item.horario} | ${item.cidade}`;
    allMassesList.appendChild(li);
  });
});
