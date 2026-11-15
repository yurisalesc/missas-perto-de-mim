import { API_BASE } from "./config.js";
import { escapeHtml } from "./lib/sanitize.js";

const WEEKDAY_OPTIONS = [
  { value: 0, label: "Segunda-feira" },
  { value: 1, label: "Terça-feira" },
  { value: 2, label: "Quarta-feira" },
  { value: 3, label: "Quinta-feira" },
  { value: 4, label: "Sexta-feira" },
  { value: 5, label: "Sábado" },
  { value: 6, label: "Domingo" },
];

const PAGE_SIZE = 25;

let auth = { user: "", pass: "" };
let editingChurchId = null;
let editingChangelogId = null;
let churchesRefreshRequestId = 0;

const pageState = {
  churches: { page: 1, total: 0 },
  suggestions: { page: 1, total: 0 },
  changelog: { page: 1, total: 0 },
};

function setAuthenticatedState(isAuthenticated) {
  document.body.classList.toggle("is-authenticated", isAuthenticated);
}

function clearAuth() {
  auth = { user: "", pass: "" };
}

function setStatus(id, text, isError = false) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.classList.toggle("is-error", Boolean(isError));
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

async function apiDownload(path) {
  const response = await fetch(`${API_BASE}${path}`, { headers: authHeader() });
  if (!response.ok) {
    const txt = await response.text();
    throw new Error(txt || `HTTP ${response.status}`);
  }
  return response.blob();
}

function clearAdminUi() {
  editingChurchId = null;
  editingChangelogId = null;
  churchesRefreshRequestId += 1;
  pageState.churches = { page: 1, total: 0 };
  pageState.suggestions = { page: 1, total: 0 };
  pageState.changelog = { page: 1, total: 0 };
  ["churchesTbody", "suggestionsTbody", "changelogTbody"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = "";
  });
  ["churchesPaginator", "suggestionsPaginator", "changelogPaginator"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = "";
  });
  const city = document.getElementById("churchSearchCity");
  const name = document.getElementById("churchSearchName");
  if (city) city.value = "";
  if (name) name.value = "";
  const csvForm = document.getElementById("csvForm");
  if (csvForm) csvForm.reset();
  closeChurchDialog();
  closeChangelogDialog();
  ["churchStatus", "suggestionStatus", "changelogStatus", "csvStatus", "exportStatus", "authStatus"].forEach(
    (id) => setStatus(id, "")
  );
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

function weekdaySelectHtml(selected = 6) {
  return WEEKDAY_OPTIONS.map(
    (day) =>
      `<option value="${day.value}" ${Number(selected) === day.value ? "selected" : ""}>${day.label}</option>`
  ).join("");
}

function timeInputValue(value) {
  if (!value) return "";
  return String(value).slice(0, 5);
}

function renderPaginator(containerId, stateKey, onChange) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const state = pageState[stateKey];
  const totalPages = Math.max(1, Math.ceil(state.total / PAGE_SIZE) || 1);
  const from = state.total === 0 ? 0 : (state.page - 1) * PAGE_SIZE + 1;
  const to = Math.min(state.page * PAGE_SIZE, state.total);
  el.innerHTML = `
    <div class="pages">${from}–${to} de ${state.total}</div>
    <div class="actions">
      <button type="button" class="secondary" data-page-action="prev" ${state.page <= 1 ? "disabled" : ""}>Anterior</button>
      <button type="button" class="secondary" data-page-action="next" ${state.page >= totalPages ? "disabled" : ""}>Próxima</button>
    </div>
  `;
  el.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.dataset.pageAction === "prev" && state.page > 1) {
        state.page -= 1;
        onChange();
      }
      if (btn.dataset.pageAction === "next" && state.page < totalPages) {
        state.page += 1;
        onChange();
      }
    });
  });
}

function addMassTimeRow(data = {}) {
  const tbody = document.getElementById("massTimesBody");
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td><select name="dia_semana">${weekdaySelectHtml(data.dia_semana ?? 6)}</select></td>
    <td><input name="horario" type="time" required value="${escapeHtml(timeInputValue(data.horario))}" /></td>
    <td><input name="observacao" value="${escapeHtml(data.observacao || "")}" /></td>
    <td><button type="button" class="danger" data-remove-row>Remover</button></td>
  `;
  tr.querySelector("[data-remove-row]").addEventListener("click", () => tr.remove());
  tbody.appendChild(tr);
}

function addConfessionTimeRow(data = {}) {
  const tbody = document.getElementById("confessionTimesBody");
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td><select name="dia_semana">${weekdaySelectHtml(data.dia_semana ?? 5)}</select></td>
    <td><input name="horario_inicio" type="time" required value="${escapeHtml(timeInputValue(data.horario_inicio))}" /></td>
    <td><input name="horario_fim" type="time" required value="${escapeHtml(timeInputValue(data.horario_fim))}" /></td>
    <td><input name="observacao" value="${escapeHtml(data.observacao || "")}" /></td>
    <td><button type="button" class="danger" data-remove-row>Remover</button></td>
  `;
  tr.querySelector("[data-remove-row]").addEventListener("click", () => tr.remove());
  tbody.appendChild(tr);
}

function updateChurchDialogTitle() {
  const title = document.getElementById("churchDialogTitle");
  if (!editingChurchId) {
    title.textContent = "Adicionar igreja";
    return;
  }
  const form = document.getElementById("churchForm");
  const nome = form.elements.nome.value.trim();
  const cidade = form.elements.cidade.value.trim();
  title.textContent = nome && cidade ? `${nome} - ${cidade}` : "Editar igreja";
}

function openChurchDialog() {
  document.getElementById("churchDialog").classList.remove("hidden");
}

function closeChurchDialog() {
  document.getElementById("churchDialog").classList.add("hidden");
  const form = document.getElementById("churchForm");
  form.reset();
  editingChurchId = null;
  document.getElementById("massTimesBody").innerHTML = "";
  document.getElementById("confessionTimesBody").innerHTML = "";
  setStatus("churchDialogStatus", "");
  document.getElementById("churchDialogTitle").textContent = "Adicionar igreja";
}

function openChangelogDialog() {
  document.getElementById("changelogDialog").classList.remove("hidden");
}

function closeChangelogDialog() {
  document.getElementById("changelogDialog").classList.add("hidden");
  document.getElementById("changelogForm").reset();
  editingChangelogId = null;
  setStatus("changelogDialogStatus", "");
  document.getElementById("changelogDialogTitle").textContent = "Adicionar atualização";
  document.getElementById("changelogSubmitBtn").textContent = "Salvar";
}

async function refreshChurches() {
  const tbody = document.getElementById("churchesTbody");
  tbody.innerHTML = "";
  const requestId = ++churchesRefreshRequestId;
  const city = document.getElementById("churchSearchCity").value.trim();
  const name = document.getElementById("churchSearchName").value.trim();
  const params = new URLSearchParams({
    page: String(pageState.churches.page),
    page_size: String(PAGE_SIZE),
  });
  if (city) params.set("cidade", city);
  if (name) params.set("nome", name);

  const data = await apiFetch(`/admin/igrejas?${params.toString()}`);
  if (requestId !== churchesRefreshRequestId) return;

  pageState.churches.total = data.total || 0;
  const maxPage = Math.max(1, Math.ceil(pageState.churches.total / PAGE_SIZE) || 1);
  if (pageState.churches.page > maxPage) {
    pageState.churches.page = maxPage;
    return refreshChurches();
  }

  (data.items || []).forEach((church) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${church.id}</td>
      <td><button type="button" class="linkish" data-action="edit">${escapeHtml(church.nome)}</button></td>
      <td>${escapeHtml(church.cidade)}</td>
      <td>${escapeHtml(church.estado || "-")}</td>
      <td>${escapeHtml(church.telefone || "-")}</td>
      <td>${escapeHtml(church.redes_sociais_site || "-")}</td>
      <td class="actions">
        <button data-action="edit" type="button" class="secondary">Editar</button>
        <button data-action="delete" type="button" class="danger">Excluir</button>
      </td>
    `;
    tr.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (btn.dataset.action === "edit") {
          await startChurchEdit(church.id);
          return;
        }
        if (!confirm(`Excluir igreja "${church.nome}"?`)) return;
        try {
          await apiFetch(`/admin/igrejas/${church.id}`, { method: "DELETE" });
          setStatus("churchStatus", "Igreja excluída.");
          refreshChurches();
        } catch (e) {
          setStatus("churchStatus", `Erro ao excluir: ${e.message}`, true);
        }
      });
    });
    tbody.appendChild(tr);
  });

  renderPaginator("churchesPaginator", "churches", refreshChurches);
}

async function startChurchEdit(churchId) {
  try {
    const church = await apiFetch(`/admin/igrejas/${churchId}`);
    editingChurchId = church.id;
    const form = document.getElementById("churchForm");
    form.elements.nome.value = church.nome || "";
    form.elements.endereco.value = church.endereco || "";
    form.elements.cidade.value = church.cidade || "";
    form.elements.estado.value = church.estado || "";
    form.elements.latitude.value = church.latitude ?? "";
    form.elements.longitude.value = church.longitude ?? "";
    form.elements.telefone.value = church.telefone || "";
    form.elements.redes_sociais_site.value = church.redes_sociais_site || "";
    form.elements.observacao.value = church.observacao || "";

    document.getElementById("massTimesBody").innerHTML = "";
    document.getElementById("confessionTimesBody").innerHTML = "";
    (church.mass_times || []).forEach((item) => addMassTimeRow(item));
    (church.confession_times || []).forEach((item) => addConfessionTimeRow(item));

    updateChurchDialogTitle();
    setStatus("churchDialogStatus", "");
    openChurchDialog();
  } catch (e) {
    setStatus("churchStatus", `Erro ao carregar igreja: ${e.message}`, true);
  }
}

function collectMassTimes() {
  return [...document.querySelectorAll("#massTimesBody tr")].map((tr) => ({
    dia_semana: Number(tr.querySelector('[name="dia_semana"]').value),
    horario: `${tr.querySelector('[name="horario"]').value}:00`,
    observacao: tr.querySelector('[name="observacao"]').value.trim() || null,
  }));
}

function collectConfessionTimes() {
  return [...document.querySelectorAll("#confessionTimesBody tr")].map((tr) => {
    const inicio = tr.querySelector('[name="horario_inicio"]').value;
    const fim = tr.querySelector('[name="horario_fim"]').value;
    return {
      dia_semana: Number(tr.querySelector('[name="dia_semana"]').value),
      horario_inicio: `${inicio}:00`,
      horario_fim: `${fim}:00`,
      observacao: tr.querySelector('[name="observacao"]').value.trim() || null,
    };
  });
}

async function refreshSuggestions() {
  const tbody = document.getElementById("suggestionsTbody");
  tbody.innerHTML = "";
  const params = new URLSearchParams({
    page: String(pageState.suggestions.page),
    page_size: String(PAGE_SIZE),
  });
  const data = await apiFetch(`/admin/sugestoes?${params.toString()}`);
  pageState.suggestions.total = data.total || 0;
  const maxPage = Math.max(1, Math.ceil(pageState.suggestions.total / PAGE_SIZE) || 1);
  if (pageState.suggestions.page > maxPage) {
    pageState.suggestions.page = maxPage;
    return refreshSuggestions();
  }

  (data.items || []).forEach((s) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${s.id}</td>
      <td>${escapeHtml(s.status)}</td>
      <td>${escapeHtml(s.nome_igreja || "-")}</td>
      <td>${escapeHtml(s.cidade || "-")}</td>
      <td>${escapeHtml(s.mensagem || "-")}</td>
      <td class="actions">
        <button data-action="approved" type="button" class="default">Aprovar</button>
        <button data-action="rejected" type="button" class="danger">Rejeitar</button>
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
          setStatus("suggestionStatus", `Sugestão #${s.id} atualizada.`);
          refreshSuggestions();
        } catch (e) {
          setStatus("suggestionStatus", `Erro ao moderar: ${e.message}`, true);
        }
      });
    });
    tbody.appendChild(tr);
  });

  renderPaginator("suggestionsPaginator", "suggestions", refreshSuggestions);
}

function badgeLabel(badge) {
  if (badge === "new") return "Novo";
  if (badge === "improved") return "Melhoria";
  if (badge === "fixed") return "Correção";
  return badge || "-";
}

function toDateTimeInputValue(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const offsetMs = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}

async function refreshChangelog() {
  const tbody = document.getElementById("changelogTbody");
  tbody.innerHTML = "";
  const params = new URLSearchParams({
    page: String(pageState.changelog.page),
    page_size: String(PAGE_SIZE),
  });
  const data = await apiFetch(`/admin/changelog?${params.toString()}`);
  pageState.changelog.total = data.total || 0;
  const maxPage = Math.max(1, Math.ceil(pageState.changelog.total / PAGE_SIZE) || 1);
  if (pageState.changelog.page > maxPage) {
    pageState.changelog.page = maxPage;
    return refreshChangelog();
  }

  (data.items || []).forEach((entry) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${entry.id}</td>
      <td><button type="button" class="linkish" data-action="edit">${escapeHtml(entry.title || "-")}</button></td>
      <td>${escapeHtml(badgeLabel(entry.badge))}</td>
      <td>${escapeHtml(toDateTimeInputValue(entry.published_at).replace("T", " ") || "-")}</td>
      <td class="actions">
        <button data-action="edit" type="button" class="secondary">Editar</button>
        <button data-action="delete" type="button" class="danger">Excluir</button>
      </td>
    `;
    tr.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (btn.dataset.action === "edit") {
          startChangelogEdit(entry);
          return;
        }
        if (!confirm(`Excluir atualização #${entry.id}?`)) return;
        try {
          await apiFetch(`/admin/changelog/${entry.id}`, { method: "DELETE" });
          setStatus("changelogStatus", "Atualização excluída.");
          if (editingChangelogId === entry.id) closeChangelogDialog();
          refreshChangelog();
        } catch (e) {
          setStatus("changelogStatus", `Erro ao excluir: ${e.message}`, true);
        }
      });
    });
    tbody.appendChild(tr);
  });

  renderPaginator("changelogPaginator", "changelog", refreshChangelog);
}

function startChangelogEdit(entry) {
  editingChangelogId = entry.id;
  const form = document.getElementById("changelogForm");
  form.elements.title.value = entry.title || "";
  form.elements.description.value = entry.description || "";
  form.elements.badge.value = entry.badge || "new";
  form.elements.published_at.value = toDateTimeInputValue(entry.published_at);
  document.getElementById("changelogDialogTitle").textContent = entry.title
    ? `Editar: ${entry.title}`
    : `Editar atualização #${entry.id}`;
  document.getElementById("changelogSubmitBtn").textContent = "Salvar alterações";
  setStatus("changelogDialogStatus", "");
  openChangelogDialog();
}

async function bootstrapData() {
  try {
    await Promise.all([refreshChurches(), refreshSuggestions(), refreshChangelog()]);
  } catch (e) {
    setStatus("authStatus", "Falha ao carregar dados. Verifique login/API.", true);
  }
}

function setupAuth() {
  setAuthenticatedState(false);

  document.getElementById("authForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    auth.user = document.getElementById("admin_user").value.trim();
    auth.pass = document.getElementById("admin_pass").value;
    try {
      await apiFetch(`/admin/igrejas?page=1&page_size=1`);
      setAuthenticatedState(true);
      setStatus("authStatus", "");
      bootstrapData();
    } catch (e) {
      setAuthenticatedState(false);
      setStatus("authStatus", `Falha no login: ${e.message}`, true);
    }
  });

  document.getElementById("logoutLink").addEventListener("click", (event) => {
    event.preventDefault();
    clearAuth();
    setAuthenticatedState(false);
    clearAdminUi();
    document.getElementById("admin_user").value = "";
    document.getElementById("admin_pass").value = "";
    setStatus("authStatus", "Sessão encerrada.");
  });
}

function setupChurchDialog() {
  document.getElementById("addChurchBtn").addEventListener("click", () => {
    closeChurchDialog();
    editingChurchId = null;
    document.getElementById("churchDialogTitle").textContent = "Adicionar igreja";
    openChurchDialog();
  });

  document.querySelectorAll("[data-close-church]").forEach((btn) => {
    btn.addEventListener("click", closeChurchDialog);
  });

  document.getElementById("addMassTimeBtn").addEventListener("click", () => addMassTimeRow());
  document.getElementById("addConfessionTimeBtn").addEventListener("click", () => addConfessionTimeRow());

  const form = document.getElementById("churchForm");
  form.elements.nome.addEventListener("input", updateChurchDialogTitle);
  form.elements.cidade.addEventListener("input", updateChurchDialogTitle);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const massTimes = collectMassTimes();
    const confessionTimes = collectConfessionTimes();

    for (const item of confessionTimes) {
      if (item.horario_fim <= item.horario_inicio) {
        setStatus("churchDialogStatus", "Em confissão, o fim deve ser depois do início.", true);
        return;
      }
    }

    const payload = {
      nome: String(data.get("nome") || "").trim(),
      endereco: String(data.get("endereco") || "").trim(),
      cidade: String(data.get("cidade") || "").trim(),
      estado: String(data.get("estado") || "").trim().toUpperCase() || null,
      latitude: Number(data.get("latitude")),
      longitude: Number(data.get("longitude")),
      telefone: String(data.get("telefone") || "").trim() || null,
      redes_sociais_site: String(data.get("redes_sociais_site") || "").trim() || null,
      observacao: String(data.get("observacao") || "").trim() || null,
      mass_times: massTimes,
      confession_times: confessionTimes,
    };

    if (!payload.nome || !payload.endereco || !payload.cidade) {
      setStatus("churchDialogStatus", "Preencha nome, endereço e cidade.", true);
      return;
    }
    if (Number.isNaN(payload.latitude) || Number.isNaN(payload.longitude)) {
      setStatus("churchDialogStatus", "Latitude e longitude precisam ser números válidos.", true);
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
      closeChurchDialog();
      refreshChurches();
    } catch (e) {
      setStatus("churchDialogStatus", `Erro ao salvar: ${e.message}`, true);
    }
  });
}

function setupChangelogDialog() {
  document.getElementById("addChangelogBtn").addEventListener("click", () => {
    closeChangelogDialog();
    openChangelogDialog();
  });
  document.querySelectorAll("[data-close-changelog]").forEach((btn) => {
    btn.addEventListener("click", closeChangelogDialog);
  });

  document.getElementById("changelogForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(event.target);
    const publishedAtRaw = String(data.get("published_at") || "").trim();
    const payload = {
      title: String(data.get("title") || "").trim(),
      description: String(data.get("description") || "").trim(),
      badge: String(data.get("badge") || "").trim(),
      published_at: publishedAtRaw || null,
    };
    if (!payload.title || !payload.description || !payload.badge) {
      setStatus("changelogDialogStatus", "Preencha título, descrição e badge.", true);
      return;
    }
    try {
      await apiFetch(editingChangelogId ? `/admin/changelog/${editingChangelogId}` : "/admin/changelog", {
        method: editingChangelogId ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setStatus(
        "changelogStatus",
        editingChangelogId ? "Atualização editada com sucesso." : "Atualização criada com sucesso."
      );
      closeChangelogDialog();
      refreshChangelog();
    } catch (e) {
      setStatus("changelogDialogStatus", `Erro ao salvar: ${e.message}`, true);
    }
  });
}

function setupCsv() {
  document.getElementById("csvForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = document.getElementById("csvFile").files[0];
    const replaceExisting = document.getElementById("replaceExisting").checked;
    if (!file) {
      setStatus("csvStatus", "Selecione um arquivo CSV.", true);
      return;
    }
    const form = new FormData();
    form.append("file", file);
    try {
      const data = await apiFetch(`/admin/importacao/csv/popular?replace_existing=${replaceExisting}`, {
        method: "POST",
        body: form,
      });
      setStatus(
        "csvStatus",
        `Importado. Igrejas: ${data.created_churches || 0}, missas: ${data.created_schedules || 0}, confissões: ${data.created_confession_schedules || 0}.`
      );
      refreshChurches();
    } catch (e) {
      setStatus("csvStatus", `Erro na importação: ${e.message}`, true);
    }
  });

  document.getElementById("exportCsvBtn").addEventListener("click", async () => {
    try {
      const blob = await apiDownload("/admin/exportacao/csv");
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "missas_export.csv";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setStatus("exportStatus", "CSV exportado com sucesso.");
    } catch (e) {
      setStatus("exportStatus", `Erro ao exportar: ${e.message}`, true);
    }
  });
}

function setupRefreshButtons() {
  document.getElementById("refreshChurches").addEventListener("click", () => {
    pageState.churches.page = 1;
    refreshChurches();
  });
  document.getElementById("refreshSuggestions").addEventListener("click", () => {
    pageState.suggestions.page = 1;
    refreshSuggestions();
  });
  document.getElementById("refreshChangelog").addEventListener("click", () => {
    pageState.changelog.page = 1;
    refreshChangelog();
  });

  const onFilter = () => {
    pageState.churches.page = 1;
    refreshChurches();
  };
  document.getElementById("churchSearchCity").addEventListener("input", onFilter);
  document.getElementById("churchSearchName").addEventListener("input", onFilter);
}

setupTabs();
setupAuth();
setupChurchDialog();
setupChangelogDialog();
setupCsv();
setupRefreshButtons();
