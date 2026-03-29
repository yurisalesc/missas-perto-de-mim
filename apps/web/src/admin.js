import { API_BASE } from "./config.js";
import { escapeHtml } from "./lib/sanitize.js";

let auth = { user: "", pass: "" };
let churchesCache = [];
let editingChurchId = null;
let churchesRefreshRequestId = 0;

function clearAuth() {
  auth = { user: "", pass: "" };
}

function setStatus(id, text, isError = false) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.style.color = isError ? "#b91c1c" : "#0b5f59";
}

function authHeader() {
  const token = btoa(`${auth.user}:${auth.pass}`);
  return { Authorization: `Basic ${token}` };
}

async function apiFetch(path, options = {}) {
  const headers = { ...(options.headers || {}), ...authHeader() };
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const txt = await response.text();
    throw new Error(txt || `HTTP ${response.status}`);
  }
  if (response.status === 204) return null;
  return response.json();
}

function setupTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("active"));
      btn.classList.add("active");
      const target = document.getElementById(`tab-${btn.dataset.tab}`);
      if (target) target.classList.add("active");
    });
  });
}

async function refreshChurches() {
  const tbody = document.getElementById("churchesTbody");
  tbody.innerHTML = "";
  const requestId = ++churchesRefreshRequestId;
  const city = document.getElementById("churchSearchCity").value.trim();
  const name = document.getElementById("churchSearchName").value.trim();
  const params = new URLSearchParams();
  if (city) params.set("cidade", city);
  if (name) params.set("nome", name);
  const path = params.toString() ? `/admin/igrejas?${params.toString()}` : "/admin/igrejas";
  const items = await apiFetch(path);
  // Ignore stale async responses to avoid duplicate render after fast typing.
  if (requestId !== churchesRefreshRequestId) return;
  churchesCache = items;
  items.forEach((church) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${church.id}</td>
      <td>${escapeHtml(church.nome)}</td>
      <td>${escapeHtml(church.cidade)}</td>
      <td>${escapeHtml(church.telefone || "-")}</td>
      <td>${escapeHtml(church.redes_sociais_site || "-")}</td>
      <td class="actions">
        <button data-action="edit" data-id="${church.id}" class="secondary">Editar</button>
        <button data-action="delete" data-id="${church.id}" class="danger">Excluir</button>
      </td>
    `;
    tr.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (btn.dataset.action === "edit") {
          startChurchEdit(church.id);
          return;
        }
        if (!confirm(`Excluir igreja #${church.id}?`)) return;
        try {
          await apiFetch(`/admin/igrejas/${church.id}`, { method: "DELETE" });
          setStatus("churchStatus", "Igreja excluida.");
          resetChurchForm();
          refreshChurches();
        } catch (e) {
          setStatus("churchStatus", `Erro ao excluir: ${e.message}`, true);
        }
      });
    });
    tbody.appendChild(tr);
  });
}

function startChurchEdit(churchId) {
  const church = churchesCache.find((c) => c.id === churchId);
  if (!church) return;
  editingChurchId = church.id;
  const form = document.getElementById("churchForm");
  form.elements.nome.value = church.nome || "";
  form.elements.endereco.value = church.endereco || "";
  form.elements.cidade.value = church.cidade || "";
  form.elements.latitude.value = church.latitude ?? "";
  form.elements.longitude.value = church.longitude ?? "";
  form.elements.telefone.value = church.telefone || "";
  form.elements.redes_sociais_site.value = church.redes_sociais_site || "";
  form.elements.observacao.value = church.observacao || "";
  document.getElementById("churchFormTitle").textContent = `Editar igreja #${church.id}`;
  document.getElementById("churchSubmitBtn").textContent = "Salvar alterações";
}

function resetChurchForm() {
  const form = document.getElementById("churchForm");
  form.reset();
  editingChurchId = null;
  document.getElementById("churchFormTitle").textContent = "Criar igreja";
  document.getElementById("churchSubmitBtn").textContent = "Salvar igreja";
}

async function refreshSchedules() {
  const tbody = document.getElementById("schedulesTbody");
  tbody.innerHTML = "";
  const items = await apiFetch("/admin/horarios");
  items.slice(0, 300).forEach((schedule) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${schedule.id}</td>
      <td>${schedule.church_id}</td>
      <td>${schedule.dia_semana}</td>
      <td>${String(schedule.horario).slice(0, 5)}</td>
      <td class="actions"><button data-id="${schedule.id}" class="danger">Excluir</button></td>
    `;
    tr.querySelector("button").addEventListener("click", async () => {
      if (!confirm(`Excluir horario #${schedule.id}?`)) return;
      try {
        await apiFetch(`/admin/horarios/${schedule.id}`, { method: "DELETE" });
        setStatus("scheduleStatus", "Horario excluido.");
        refreshSchedules();
      } catch (e) {
        setStatus("scheduleStatus", `Erro ao excluir: ${e.message}`, true);
      }
    });
    tbody.appendChild(tr);
  });
}

async function refreshSuggestions() {
  const tbody = document.getElementById("suggestionsTbody");
  tbody.innerHTML = "";
  const items = await apiFetch("/admin/sugestoes");
  items.forEach((s) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${s.id}</td>
      <td>${escapeHtml(s.status)}</td>
      <td>${escapeHtml(s.nome_igreja || "-")}</td>
      <td>${escapeHtml(s.cidade || "-")}</td>
      <td>${escapeHtml(s.mensagem || "-")}</td>
      <td class="actions">
        <button data-action="approved">Aprovar</button>
        <button data-action="rejected" class="danger">Rejeitar</button>
      </td>
    `;
    tr.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", async () => {
        try {
          await apiFetch(`/admin/sugestoes/${s.id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: btn.dataset.action }),
          });
          setStatus("suggestionStatus", `Sugestao #${s.id} atualizada.`);
          refreshSuggestions();
        } catch (e) {
          setStatus("suggestionStatus", `Erro ao moderar: ${e.message}`, true);
        }
      });
    });
    tbody.appendChild(tr);
  });
}

async function bootstrapData() {
  try {
    await Promise.all([refreshChurches(), refreshSchedules(), refreshSuggestions()]);
  } catch (e) {
    setStatus("authStatus", "Falha ao carregar dados. Verifique login/API.", true);
  }
}

function setupAuth() {
  document.getElementById("admin_user").value = auth.user || "";
  document.getElementById("admin_pass").value = auth.pass || "";

  document.getElementById("authForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    auth.user = document.getElementById("admin_user").value.trim();
    auth.pass = document.getElementById("admin_pass").value;
    try {
      await apiFetch("/admin/igrejas");
      setStatus("authStatus", "Autenticado com sucesso.");
      bootstrapData();
    } catch (e) {
      setStatus("authStatus", `Falha no login: ${e.message}`, true);
    }
  });

  document.getElementById("logoutBtn").addEventListener("click", () => {
    clearAuth();
    document.getElementById("admin_user").value = "";
    document.getElementById("admin_pass").value = "";
    setStatus("authStatus", "Credenciais removidas.");
  });
}

function setupForms() {
  document.getElementById("churchForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(event.target);
    const payload = {
      nome: String(data.get("nome") || "").trim(),
      endereco: String(data.get("endereco") || "").trim(),
      cidade: String(data.get("cidade") || "").trim(),
      latitude: Number(data.get("latitude")),
      longitude: Number(data.get("longitude")),
      telefone: String(data.get("telefone") || "").trim() || null,
      redes_sociais_site: String(data.get("redes_sociais_site") || "").trim() || null,
      observacao: String(data.get("observacao") || "").trim() || null,
    };
    if (!payload.nome || !payload.endereco || !payload.cidade) {
      setStatus("churchStatus", "Preencha nome, endereco e cidade.", true);
      return;
    }
    if (Number.isNaN(payload.latitude) || Number.isNaN(payload.longitude)) {
      setStatus("churchStatus", "Latitude e longitude precisam ser numeros validos.", true);
      return;
    }
    try {
      await apiFetch(editingChurchId ? `/admin/igrejas/${editingChurchId}` : "/admin/igrejas", {
        method: editingChurchId ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setStatus(
        "churchStatus",
        editingChurchId ? "Igreja atualizada com sucesso." : "Igreja criada com sucesso."
      );
      resetChurchForm();
      refreshChurches();
    } catch (e) {
      setStatus("churchStatus", `Erro ao salvar: ${e.message}`, true);
    }
  });

  document.getElementById("churchCancelEditBtn").addEventListener("click", resetChurchForm);

  document.getElementById("scheduleForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(event.target);
    const payload = {
      church_id: Number(data.get("church_id")),
      dia_semana: Number(data.get("dia_semana")),
      horario: `${String(data.get("horario"))}:00`,
      observacao: String(data.get("observacao") || "").trim() || null,
    };
    try {
      await apiFetch("/admin/horarios", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setStatus("scheduleStatus", "Horario criado com sucesso.");
      event.target.reset();
      refreshSchedules();
    } catch (e) {
      setStatus("scheduleStatus", `Erro ao criar: ${e.message}`, true);
    }
  });

  document.getElementById("csvForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = document.getElementById("csvFile").files[0];
    if (!file) {
      setStatus("csvStatus", "Selecione um arquivo CSV.", true);
      return;
    }
    const form = new FormData();
    form.append("file", file);
    try {
      const data = await apiFetch("/admin/importacao/csv", { method: "POST", body: form });
      setStatus(
        "csvStatus",
        `Importado. Igrejas: ${data.created_churches || 0}, horarios: ${data.created_schedules || 0}.`
      );
      refreshChurches();
      refreshSchedules();
    } catch (e) {
      setStatus("csvStatus", `Erro na importacao: ${e.message}`, true);
    }
  });
}

function setupRefreshButtons() {
  document.getElementById("refreshChurches").addEventListener("click", refreshChurches);
  document.getElementById("refreshSchedules").addEventListener("click", refreshSchedules);
  document.getElementById("refreshSuggestions").addEventListener("click", refreshSuggestions);
  document.getElementById("churchSearchCity").addEventListener("input", refreshChurches);
  document.getElementById("churchSearchName").addEventListener("input", refreshChurches);
}

setupTabs();
setupAuth();
setupForms();
setupRefreshButtons();

