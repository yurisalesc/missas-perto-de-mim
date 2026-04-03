import { API_BASE } from "./config.js";
import { escapeHtml } from "./lib/sanitize.js";
import { weekdayNamePt } from "./lib/time.js";

let currentCoords = null;
const citySuggestions = document.getElementById("citySuggestions");

function ensureLeaflet() {
  if (window.L) return true;
  alert(
    "Não foi possível carregar o mapa (Leaflet). " +
      "Verifique sua internet ou libere o acesso a unpkg.com."
  );
  return false;
}

let map = null;
if (ensureLeaflet()) {
  map = L.map("map").setView([-5.7945, -35.211], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);
}

const markers = [];
let userLocationMarker = null;
const resultsTbody = document.getElementById("resultsTbody");
const homeResultsLegend = document.getElementById("homeResultsLegend");
const homeResultsMessage = document.getElementById("homeResultsMessage");
const homeResultsTableWrap = document.getElementById("homeResultsTableWrap");
const locationStatus = document.getElementById("locationStatus");
const allMassesTbody = document.getElementById("allMassesTbody");
const allMassesTableWrap = document.getElementById("allMassesTableWrap");
const allMassesMessage = document.getElementById("allMassesMessage");
const resultsNowTbody = document.getElementById("resultsNowTbody");
const nowResultsTableWrap = document.getElementById("nowResultsTableWrap");
const nowResultsMessage = document.getElementById("nowResultsMessage");
const cityByStateSection = document.getElementById("cityByStateSection");
const cityByStateContent = document.getElementById("cityByStateContent");

function clearMarkers() {
  markers.forEach((marker) => marker.remove());
  markers.length = 0;
}

function fitMarkers() {
  if (!map || markers.length === 0) return;
  if (markers.length === 1) {
    map.setView(markers[0].getLatLng(), 14);
    return;
  }
  const bounds = L.latLngBounds(markers.map((m) => m.getLatLng()));
  map.fitBounds(bounds, { padding: [20, 20] });
}

function plotChurches(churches) {
  clearMarkers();
  if (!map) return;
  (churches || []).forEach((church) => {
    const marker = L.marker([church.latitude, church.longitude]).addTo(map);
    marker.bindPopup(`${escapeHtml(church.nome)}<br>${escapeHtml(church.endereco)}`);
    markers.push(marker);
  });
  fitMarkers();
}

function showOnlyChurchOnMap(church) {
  clearMarkers();
  if (!map) return;
  const marker = L.marker([church.latitude, church.longitude]).addTo(map);
  marker.bindPopup(`${church.nome}<br>${church.endereco}`).openPopup();
  markers.push(marker);
  fitMarkers();
  setActiveTab("tab-home");
}

function formatOccurrenceHour(occurrenceIso, fallbackHorario) {
  if (occurrenceIso) {
    const d = new Date(occurrenceIso);
    const hh = String(d.getHours()).padStart(2, "0");
    const mm = String(d.getMinutes()).padStart(2, "0");
    return `${hh}:${mm}`;
  }
  return String(fallbackHorario || "").substring(0, 5);
}

function getContactInfo(church) {
  const fallback = "Não informado";
  const telefone = church?.telefone || fallback;
  const redesSociaisSite = church?.redes_sociais_site || fallback;
  const observacao = church?.observacao || church?.proximas_missas?.[0]?.observacao || fallback;
  return { telefone, redesSociaisSite, observacao };
}

function updateLocationStatus() {
  if (!locationStatus) return;
  const hasCoords = Boolean(currentCoords);
  const city = document.getElementById("city").value.trim();
  if (hasCoords && city) {
    locationStatus.textContent = "Filtro ativo: cidade + sua localização.";
    locationStatus.classList.remove("muted");
    return;
  }
  if (hasCoords) {
    locationStatus.textContent = "Filtro ativo: sua localização.";
    locationStatus.classList.remove("muted");
    return;
  }
  locationStatus.textContent = "Você pode combinar cidade + localização para refinar os resultados.";
  locationStatus.classList.add("muted");
}

function applyAllMassesDayColumnVisibility(selectedDay) {
  const dayColumns = document.querySelectorAll(".day-col");
  dayColumns.forEach((cell) => {
    const keepVisible = selectedDay === "" || cell.classList.contains(`day-${selectedDay}`);
    cell.style.display = keepVisible ? "" : "none";
  });
}

function sortByEarliestOccurrence(churches) {
  return [...(churches || [])].sort((a, b) => {
    const aFirst = a?.proximas_missas?.[0]?.ocorrencia_em || "";
    const bFirst = b?.proximas_missas?.[0]?.ocorrencia_em || "";
    return aFirst.localeCompare(bFirst);
  });
}

function appendChurchResultRow(targetTbody, church) {
  const tr = document.createElement("tr");
  const masses = (church.proximas_missas || [])
    .map((mass) => formatOccurrenceHour(mass.ocorrencia_em, mass.horario))
    .join(" | ");
  const mapBtn = `<button type="button" data-map-id="${church.church_id}">Ver no mapa</button>`;
  const infoBtn = `<button type="button" data-info-id="${church.church_id}" class="secondary">Info</button>`;
  tr.innerHTML = `
    <td>${escapeHtml(church.nome)}</td>
    <td>${escapeHtml(church.cidade)}</td>
    <td>${escapeHtml(church.endereco)}</td>
    <td>${typeof church.distancia_km === "number" ? `${Number(church.distancia_km).toFixed(1)} km` : "-"}</td>
    <td>${escapeHtml(masses || "-")}</td>
    <td><div class="table-actions">${mapBtn}${infoBtn}</div></td>
  `;
  tr.querySelector("button").addEventListener("click", () => showOnlyChurchOnMap(church));
  const infoButton = tr.querySelector('[data-info-id]');
  infoButton.addEventListener("click", () => {
    const existing = targetTbody.querySelector(`tr[data-info-for="${church.church_id}"]`);
    if (existing) {
      existing.remove();
      return;
    }
    const infoRow = document.createElement("tr");
    infoRow.className = "info-row";
    infoRow.setAttribute("data-info-for", String(church.church_id));
    const contact = getContactInfo(church);
    infoRow.innerHTML = `
      <td colspan="6">
        <div class="info-box">
          <div><strong>Telefone:</strong> ${escapeHtml(contact.telefone)}</div>
          <div><strong>Redes sociais / Site:</strong> ${escapeHtml(contact.redesSociaisSite)}</div>
          <div><strong>Observação:</strong> ${escapeHtml(contact.observacao)}</div>
        </div>
      </td>
    `;
    tr.insertAdjacentElement("afterend", infoRow);
  });
  targetTbody.appendChild(tr);
}

async function runSearchHome() {
  const city = document.getElementById("city").value.trim();
  const radius = document.getElementById("radius").value;
  const nextHours = document.getElementById("hours").value;
  const params = new URLSearchParams();
  params.set("radius_km", radius);
  params.set("next_hours", nextHours);
  if (city) params.set("city", city);
  if (currentCoords) {
    params.set("lat", String(currentCoords.lat));
    params.set("lon", String(currentCoords.lon));
  }
  const response = await fetch(`${API_BASE}/igrejas/buscar?${params.toString()}`);
  const payloadRaw = await response.json();
  const payload = sortByEarliestOccurrence(payloadRaw);
  resultsTbody.innerHTML = "";
  homeResultsTableWrap.classList.remove("hidden");
  homeResultsMessage.textContent = "";
  if (!Array.isArray(payload) || payload.length === 0) {
    homeResultsTableWrap.classList.add("hidden");
    homeResultsLegend.textContent = "";
    homeResultsMessage.textContent =
      "Não encontramos missas para esse período agora. Tente aumentar as horas ou ajustar seus filtros.";
    homeResultsMessage.style.color = "#b91c1c";
    plotChurches([]);
    return;
  }

  const now = new Date();
  const startDate = now;
  const startHour = `${String(startDate.getHours()).padStart(2, "0")}:${String(startDate.getMinutes()).padStart(
    2,
    "0"
  )}`;
  const startWeekday = weekdayNamePt(startDate);
  homeResultsLegend.textContent = `Missas a partir das ${startHour} de ${startWeekday}`;
  homeResultsLegend.style.color = "#0b5f59";
  homeResultsMessage.textContent = "";
  payload.forEach((church) => appendChurchResultRow(resultsTbody, church));
  plotChurches(payload);
}

async function runSearchNow() {
  const city = document.getElementById("city_now").value.trim();
  const params = new URLSearchParams();
  if (city) params.set("city", city);
  const response = await fetch(`${API_BASE}/igrejas/acontecendo-agora?${params.toString()}`);
  const payloadRaw = await response.json();
  const payload = sortByEarliestOccurrence(payloadRaw);
  resultsNowTbody.innerHTML = "";
  nowResultsTableWrap.classList.remove("hidden");
  nowResultsMessage.textContent = "";
  if (!Array.isArray(payload) || payload.length === 0) {
    nowResultsTableWrap.classList.add("hidden");
    nowResultsMessage.textContent = "Nenhuma missa acontecendo agora para esta cidade.";
    nowResultsMessage.style.color = "#b91c1c";
    plotChurches([]);
    return;
  }
  payload.forEach((church) => appendChurchResultRow(resultsNowTbody, church));
  plotChurches(payload);
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
      if (map) {
        map.setView([currentCoords.lat, currentCoords.lon], 13);
        if (userLocationMarker) {
          userLocationMarker.setLatLng([currentCoords.lat, currentCoords.lon]);
        } else {
          userLocationMarker = L.circleMarker([currentCoords.lat, currentCoords.lon], {
            radius: 9,
            color: "#dc2626",
            fillColor: "#ef4444",
            fillOpacity: 0.95,
            weight: 2,
          })
            .addTo(map)
            .bindPopup("Sua localização");
        }
      }
      updateLocationStatus();
    },
    (error) => {
      alert("Não foi possível obter sua localização. Verifique as permissões e tente novamente.");
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
});

document.getElementById("clear_geo").addEventListener("click", () => {
  currentCoords = null;
  if (userLocationMarker) {
    userLocationMarker.remove();
    userLocationMarker = null;
  }
  updateLocationStatus();
});

document.getElementById("search").addEventListener("click", runSearchHome);
document.getElementById("search_now").addEventListener("click", runSearchNow);

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/src/sw.js");
}

document.querySelectorAll(".suggestionForm").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const statusSel = form.getAttribute("data-status");
    const context = form.getAttribute("data-context") || "geral";
    const statusEl = statusSel ? document.querySelector(statusSel) : null;
    if (statusEl) statusEl.textContent = "Enviando...";
    const formData = new FormData(form);
    const mensagem = String(formData.get("mensagem") || "").trim();
    const payload = {
      nome_igreja: "Feedback de usuário",
      endereco: "Não informado",
      cidade: "Não informado",
      mensagem: `[${context}] ${mensagem}` || null,
    };
    try {
      const response = await fetch(`${API_BASE}/sugestoes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error(await response.text());
      if (statusEl) statusEl.textContent = "Feedback enviado para moderação. Obrigado!";
      form.reset();
    } catch (e) {
      if (statusEl) statusEl.textContent = "Falha ao enviar. Tente novamente.";
    }
  });
});

document.getElementById("listar_todas").addEventListener("click", async () => {
  allMassesTbody.innerHTML = "";
  const cidade = document.getElementById("filtro_cidade").value.trim();
  const nomeIgreja = document.getElementById("filtro_igreja").value.trim();
  const diaSemana = document.getElementById("filtro_dia_semana").value;
  if (!cidade && !nomeIgreja && diaSemana === "") {
    allMassesTableWrap.classList.add("hidden");
    allMassesMessage.textContent = "Aplique ao menos um filtro para exibir resultados.";
    return;
  }

  allMassesTableWrap.classList.remove("hidden");
  allMassesMessage.textContent = "";

  const params = new URLSearchParams();
  if (cidade) params.set("cidade", cidade);
  if (nomeIgreja) params.set("nome_igreja", nomeIgreja);
  if (diaSemana !== "") params.set("dia_semana", diaSemana);
  const response = await fetch(`${API_BASE}/missas/todas?${params.toString()}`);
  const payload = await response.json();
  if (!Array.isArray(payload) || payload.length === 0) {
    allMassesTableWrap.classList.add("hidden");
    allMassesMessage.textContent = "Nenhuma missa encontrada para os filtros informados.";
    return;
  }

  const grouped = new Map();
  payload.forEach((item) => {
    const key = `${item.cidade}||${item.nome_igreja}`;
    if (!grouped.has(key)) {
      grouped.set(key, {
        cidade: item.cidade,
        nome_igreja: item.nome_igreja,
        telefone: item.telefone || null,
        redes_sociais_site: item.redes_sociais_site || null,
        observacao: item.observacao || null,
        dias: { 0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [] },
      });
    }
    const current = grouped.get(key);
    current.dias[item.dia_semana].push(String(item.horario).substring(0, 5));
    if (!current.telefone && item.telefone) current.telefone = item.telefone;
    if (!current.redes_sociais_site && item.redes_sociais_site) current.redes_sociais_site = item.redes_sociais_site;
    if (!current.observacao && item.observacao) current.observacao = item.observacao;
  });

  const sortTimes = (times) =>
    [...new Set(times)].sort((a, b) => {
      const [ah, am] = a.split(":").map(Number);
      const [bh, bm] = b.split(":").map(Number);
      return ah * 60 + am - (bh * 60 + bm);
    });

  Array.from(grouped.values()).forEach((row) => {
    for (let i = 0; i <= 6; i += 1) {
      row.dias[i] = sortTimes(row.dias[i]);
    }
    const tr = document.createElement("tr");
    const infoBtn = `<button type="button" class="secondary" data-all-info="1">Info</button>`;
    tr.innerHTML = `
      <td>${escapeHtml(row.cidade)}</td>
      <td>${escapeHtml(row.nome_igreja)}</td>
      <td class="day-col day-0">${escapeHtml(row.dias[0].join(", ") || "-")}</td>
      <td class="day-col day-1">${escapeHtml(row.dias[1].join(", ") || "-")}</td>
      <td class="day-col day-2">${escapeHtml(row.dias[2].join(", ") || "-")}</td>
      <td class="day-col day-3">${escapeHtml(row.dias[3].join(", ") || "-")}</td>
      <td class="day-col day-4">${escapeHtml(row.dias[4].join(", ") || "-")}</td>
      <td class="day-col day-5">${escapeHtml(row.dias[5].join(", ") || "-")}</td>
      <td class="day-col day-6">${escapeHtml(row.dias[6].join(", ") || "-")}</td>
      <td><div class="table-actions">${infoBtn}</div></td>
    `;
    tr.querySelector('[data-all-info="1"]').addEventListener("click", () => {
      const existing = tr.nextElementSibling;
      if (existing && existing.classList.contains("info-row")) {
        existing.remove();
        return;
      }
      const infoRow = document.createElement("tr");
      infoRow.className = "info-row";
      infoRow.innerHTML = `
        <td colspan="10">
          <div class="info-box">
            <div><strong>Telefone:</strong> ${escapeHtml(row.telefone || "Não informado")}</div>
            <div><strong>Redes sociais / Site:</strong> ${escapeHtml(row.redes_sociais_site || "Não informado")}</div>
            <div><strong>Observação:</strong> ${escapeHtml(row.observacao || "Não informado")}</div>
          </div>
        </td>
      `;
      tr.insertAdjacentElement("afterend", infoRow);
    });
    allMassesTbody.appendChild(tr);
  });
  applyAllMassesDayColumnVisibility(diaSemana);
});

async function loadCitySuggestions(query = "") {
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  params.set("limit", "20");
  const response = await fetch(`${API_BASE}/igrejas/cidades?${params.toString()}`);
  if (!response.ok) return;
  const cities = await response.json();
  citySuggestions.innerHTML = "";
  (cities || []).forEach((city) => {
    const option = document.createElement("option");
    option.value = city;
    citySuggestions.appendChild(option);
  });
}

async function loadCitiesByStateSection() {
  if (!cityByStateContent) return;
  const response = await fetch(`${API_BASE}/igrejas/cidades-por-estado`);
  if (!response.ok) return;
  const groups = await response.json();
  cityByStateContent.innerHTML = "";
  Object.entries(groups || {}).forEach(([state, cities]) => {
    const block = document.createElement("div");
    block.className = "city-state-block";
    block.innerHTML = `
      <div class="city-state-title">${escapeHtml(state)}</div>
      <div class="city-state-list">${escapeHtml((cities || []).join(" | "))}</div>
    `;
    cityByStateContent.appendChild(block);
  });
}

["city", "filtro_cidade", "city_now"].forEach((id) => {
  const input = document.getElementById(id);
  input.addEventListener("input", () => loadCitySuggestions(input.value.trim()));
  input.addEventListener("focus", () => loadCitySuggestions(input.value.trim()));
});
document.getElementById("city").addEventListener("input", updateLocationStatus);
loadCitySuggestions();
loadCitiesByStateSection();
updateLocationStatus();

function setActiveTab(tabId) {
  const tabs = [
    { btn: document.getElementById("tab-home"), panel: document.getElementById("panel-home") },
    { btn: document.getElementById("tab-all"), panel: document.getElementById("panel-all") },
    { btn: document.getElementById("tab-now"), panel: document.getElementById("panel-now") },
    { btn: document.getElementById("tab-confessions"), panel: document.getElementById("panel-confessions") },
  ];
  tabs.forEach(({ btn, panel }) => {
    if (!btn || !panel) return;
    const active = btn.id === tabId;
    btn.setAttribute("aria-selected", active ? "true" : "false");
    panel.classList.toggle("active", active);
  });
}

document.getElementById("tab-home").addEventListener("click", () => setActiveTab("tab-home"));
document.getElementById("tab-all").addEventListener("click", () => setActiveTab("tab-all"));
document.getElementById("tab-now").addEventListener("click", () => setActiveTab("tab-now"));
document.getElementById("toggleCitiesButton").addEventListener("click", () => {
  if (!cityByStateSection) return;
  cityByStateSection.classList.toggle("hidden");
});
document.getElementById("filtro_dia_semana").addEventListener("change", (event) => {
  applyAllMassesDayColumnVisibility(event.target.value);
});

document.getElementById("addCityCta").addEventListener("click", (event) => {
  event.preventDefault();
  setActiveTab("tab-home");
  document.getElementById("feedback_home").scrollIntoView({ behavior: "smooth", block: "start" });
});
