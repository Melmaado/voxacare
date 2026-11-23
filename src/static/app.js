// Voxacare web front: calls the FastAPI routes and renders the pages.

// ---------- Labels ----------
const PROFESSIONS = {
  nurse: "Infirmier·ère", doctor: "Médecin", occupational_therapist: "Ergothérapeute",
  physiotherapist: "Kinésithérapeute", dietitian: "Diététicien·ne", social_worker: "Assistant·e social·e", other: "Autre",
};
const DOMAINS = {
  collaboration: "Collaboration", behaviour: "Comportement", slowness: "Lenteur", continence: "Continence",
  eating_swallowing: "Repas et déglutition", hygiene: "Hygiène", organisation: "Organisation",
  initiating_interactions: "Initiation des interactions", activity_participation: "Participation aux activités",
  sociability: "Sociabilité", physical_health: "Santé physique", other: "Autre",
};
const TYPES = {
  observation: "Observation", intervention: "Soin", medication: "Médicament", refusal: "Refus", instruction: "Consigne",
};
const STATUSES = { done: "Fait", planned: "Prévu" };

// ---------- Helpers ----------
const $ = (sel) => document.querySelector(sel);

// Every value coming from the API (dictations, names) is escaped before display: no HTML injection.
function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function options(map, selected) {
  return Object.entries(map)
    .map(([value, label]) => `<option value="${value}"${value === selected ? " selected" : ""}>${esc(label)}</option>`)
    .join("");
}

async function api(path, body) {
  const init = body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  };
  const response = await fetch(path, init);
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    let detail = data && data.detail;
    if (Array.isArray(detail)) detail = detail.map((d) => d.msg).join(" ; ");
    throw new Error(detail || `Erreur ${response.status}`);
  }
  return data;
}

function notice(target, kind, text) {
  target.innerHTML = text ? `<div class="notice ${kind}">${esc(text)}</div>` : "";
}

function setLoading(button, loading, label) {
  button.disabled = loading;
  button.innerHTML = loading ? `<span class="spinner"></span>${esc(label)}` : esc(label);
}

function store(key, value) { try { sessionStorage.setItem(key, value); } catch (e) {} }
function recall(key) { try { return sessionStorage.getItem(key); } catch (e) { return null; } }

// ---------- State ----------
const state = { patientId: null, patient: null, events: [], view: "domain" };

// ---------- Who is dictating ----------
const authorInput = $("#author");
const professionSelect = $("#profession");
professionSelect.innerHTML = options(PROFESSIONS, recall("profession") || "nurse");
authorInput.value = recall("author") || "";
authorInput.addEventListener("input", () => store("author", authorInput.value));
professionSelect.addEventListener("change", () => store("profession", professionSelect.value));

// ---------- Home ----------
async function showHome() {
  state.patientId = null;
  $("#view-patient").classList.add("hidden");
  $("#view-home").classList.remove("hidden");
  const grid = $("#patient-grid");
  grid.innerHTML = "";
  $("#home-status").innerHTML = `<p class="muted"><span class="spinner dark"></span>Chargement des patients…</p>`;
  try {
    const list = await api("/patients");
    const files = await Promise.all(list.map((p) => api(`/patients/${encodeURIComponent(p.patient_id)}`)));
    $("#home-status").innerHTML = "";
    if (!files.length) {
      grid.innerHTML = `<div class="card empty">Aucun patient. Lancez <code>python src/seed.py</code>.</div>`;
      return;
    }
    grid.innerHTML = files.map((p) => {
      const open = p.instructions.filter((i) => i.status === "open").length;
      const planned = p.entries.filter((e) => e.status === "planned").length;
      return `
        <button class="patient-card" data-id="${esc(p.patient_id)}">
          <div class="name">${esc(p.pseudonym)}</div>
          <div class="meta">${esc(p.age)} ans · ${esc(p.ward)} · chambre ${esc(p.room)}</div>
          <div class="reason">${esc(p.reason_for_stay)}</div>
          <div class="badges">
            ${open ? `<span class="chip coral">${open} consigne${open > 1 ? "s" : ""} ouverte${open > 1 ? "s" : ""}</span>` : ""}
            ${planned ? `<span class="chip coral">${planned} action${planned > 1 ? "s" : ""} prévue${planned > 1 ? "s" : ""}</span>` : ""}
            <span class="chip grey">${p.entries.length} entrée${p.entries.length > 1 ? "s" : ""}</span>
          </div>
        </button>`;
    }).join("");
    grid.querySelectorAll(".patient-card").forEach((card) =>
      card.addEventListener("click", () => openPatient(card.dataset.id)));
  } catch (err) {
    notice($("#home-status"), "error", `Impossible de charger les patients : ${err.message}`);
  }
}

// ---------- Patient ----------
async function openPatient(patientId) {
  state.patientId = patientId;
  state.events = [];
  $("#view-home").classList.add("hidden");
  $("#view-patient").classList.remove("hidden");
  $("#dictation").value = "";
  $("#review").classList.add("hidden");
  $("#qa").innerHTML = "";
  ["#dictate-status", "#save-status", "#ask-status"].forEach((s) => ($(s).innerHTML = ""));
  showTab("dictate");
  await refreshPatient();
}

async function refreshPatient() {
  try {
    const p = await api(`/patients/${encodeURIComponent(state.patientId)}`);
    state.patient = p;
    $("#p-name").textContent = p.pseudonym;
    $("#p-meta").textContent = `${p.age} ans · ${p.ward} · chambre ${p.room} · ${p.reason_for_stay}`;
    const open = p.instructions.filter((i) => i.status === "open").length;
    const planned = p.entries.filter((e) => e.status === "planned").length;
    $("#p-badges").innerHTML =
      (p.allergies.length ? `<span class="chip red">Allergie : ${esc(p.allergies.join(", "))}</span>` : "") +
      (open ? `<span class="chip coral">${open} consigne${open > 1 ? "s" : ""} ouverte${open > 1 ? "s" : ""}</span>` : "") +
      (planned ? `<span class="chip coral">${planned} action${planned > 1 ? "s" : ""} prévue${planned > 1 ? "s" : ""}</span>` : "");
    renderFile();
  } catch (err) {
    notice($("#file-status"), "error", `Impossible de charger le dossier : ${err.message}`);
  }
}

function showTab(name) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  ["dictate", "file", "ask"].forEach((t) => $(`#tab-${t}`).classList.toggle("hidden", t !== name));
}
document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => showTab(t.dataset.tab)));

// ---------- Dictate: extract, review, save ----------
$("#extract-btn").addEventListener("click", async () => {
  const dictation = $("#dictation").value.trim();
  const status = $("#dictate-status");
  notice($("#save-status"), "", "");
  if (dictation.length < 10) {
    notice(status, "error", "La dictée est trop courte.");
    return;
  }
  const btn = $("#extract-btn");
  setLoading(btn, true, "Analyse…");
  notice(status, "", "");
  try {
    state.events = await api(`/patients/${encodeURIComponent(state.patientId)}/extract`, { dictation });
    if (!state.events.length) {
      notice(status, "warning", "Aucune information de soin trouvée dans cette dictée.");
      $("#review").classList.add("hidden");
    } else {
      renderReview();
    }
  } catch (err) {
    notice(status, "error", `L'analyse a échoué : ${err.message}`);
  } finally {
    setLoading(btn, false, "Analyser");
  }
});

function renderReview() {
  $("#review").classList.remove("hidden");
  $("#review-list").innerHTML = state.events.map((e, i) => {
    const extra = [e.time && `heure : ${e.time}`, e.drug && `médicament : ${e.drug}`, e.dose && `dose : ${e.dose}`, e.route && `voie : ${e.route}`]
      .filter(Boolean).join(" · ");
    return `
      <div class="event ${e.status === "planned" ? "planned" : ""}" data-index="${i}">
        <div>
          <input type="text" data-field="content" value="${esc(e.content)}" aria-label="Contenu">
          <div class="event-fields">
            <label>Type<select data-field="type">${options(TYPES, e.type)}</select></label>
            <label>Domaine<select data-field="domain">${options(DOMAINS, e.domain)}</select></label>
            <label>Statut<select data-field="status">${options(STATUSES, e.status)}</select></label>
          </div>
          ${extra ? `<div class="extra">${esc(extra)}</div>` : ""}
        </div>
        <button class="btn-icon" data-remove="${i}" title="Supprimer cette entrée" aria-label="Supprimer cette entrée">×</button>
      </div>`;
  }).join("");

  $("#review-list").querySelectorAll("[data-field]").forEach((field) => {
    const sync = () => {
      const index = Number(field.closest(".event").dataset.index);
      state.events[index][field.dataset.field] = field.value;
      if (field.dataset.field === "status") field.closest(".event").classList.toggle("planned", field.value === "planned");
    };
    field.addEventListener("input", sync);
    field.addEventListener("change", sync);
  });
  $("#review-list").querySelectorAll("[data-remove]").forEach((btn) =>
    btn.addEventListener("click", () => {
      state.events.splice(Number(btn.dataset.remove), 1);
      if (state.events.length) renderReview(); else $("#review").classList.add("hidden");
    }));
}

$("#cancel-btn").addEventListener("click", () => {
  state.events = [];
  $("#review").classList.add("hidden");
});

// Entries are saved only here, when the caregiver clicks "Valider et enregistrer".
$("#save-btn").addEventListener("click", async () => {
  const status = $("#save-status");
  const author = authorInput.value.trim();
  if (!author) {
    notice(status, "error", "Indiquez votre nom dans « Qui dicte ? » avant d'enregistrer.");
    authorInput.focus();
    return;
  }
  if (state.events.some((e) => !String(e.content).trim())) {
    notice(status, "error", "Une entrée est vide : complétez-la ou supprimez-la.");
    return;
  }
  const btn = $("#save-btn");
  setLoading(btn, true, "Enregistrement…");
  try {
    const saved = await api(`/patients/${encodeURIComponent(state.patientId)}/entries`, {
      events: state.events, author, profession: professionSelect.value,
    });
    state.events = [];
    $("#review").classList.add("hidden");
    $("#dictation").value = "";
    notice($("#dictate-status"), "success",
      `${saved.length} entrée${saved.length > 1 ? "s" : ""} enregistrée${saved.length > 1 ? "s" : ""} (${saved.map((e) => e.id).join(", ")}).`);
    await refreshPatient();
  } catch (err) {
    notice(status, "error", `L'enregistrement a échoué : ${err.message}`);
  } finally {
    setLoading(btn, false, "Valider et enregistrer");
  }
});

// ---------- File ----------
document.querySelectorAll(".view-toggle button").forEach((b) =>
  b.addEventListener("click", () => {
    state.view = b.dataset.view;
    document.querySelectorAll(".view-toggle button").forEach((x) => x.classList.toggle("active", x === b));
    renderEntries();
  }));

function listOrNone(items) {
  return items.length ? `<ul>${items.join("")}</ul>` : `<p class="muted small" style="margin:0">Rien d'enregistré</p>`;
}

function renderFile() {
  const p = state.patient;
  $("#summary").innerHTML = `
    <div class="card">
      <h3>Diagnostics</h3>
      ${listOrNone(p.diagnoses.map((d) => `<li>${esc(d)}</li>`))}
      <h3 style="margin-top:14px">Antécédents</h3>
      ${listOrNone(p.medical_history.map((d) => `<li>${esc(d)}</li>`))}
    </div>
    <div class="card">
      <h3>Allergies</h3>
      ${p.allergies.length ? `<div class="badges">${p.allergies.map((a) => `<span class="chip red">${esc(a)}</span>`).join("")}</div>`
                           : `<p class="muted small" style="margin:0">Aucune allergie enregistrée</p>`}
      <h3 style="margin-top:14px">Traitements prescrits</h3>
      ${listOrNone(p.treatments.map((t, i) =>
        `<li id="ref-T${i + 1}"><span class="chip id">T${i + 1}</span> ${esc(t.drug)} ${esc(t.dose)} ${esc(t.route || "")} <span class="muted">${esc(t.frequency || "")}</span></li>`))}
    </div>
    <div class="card">
      <h3>Consignes</h3>
      ${listOrNone(p.instructions.map((ins) =>
        `<li id="ref-${esc(ins.id)}" class="instruction ${ins.status === "open" ? "open" : ""}">
           <span class="chip id">${esc(ins.id)}</span>
           <span class="chip ${ins.status === "open" ? "coral" : "grey"}">${ins.status === "open" ? "ouverte" : "faite"}</span>
           ${esc(ins.text)} <span class="muted small">(${esc(ins.author)}, ${esc(ins.date)})</span>
         </li>`))}
    </div>`;
  renderEntries();
}

function entryHtml(e) {
  const details = [e.drug, e.dose, e.route].filter(Boolean).join(" ");
  return `
    <div class="entry ${e.status === "planned" ? "planned" : ""}" id="ref-${esc(e.id)}">
      <div class="entry-top">
        <span class="chip id">${esc(e.id)}</span>
        ${e.status === "planned" ? `<span class="chip coral">Prévu</span>` : ""}
        <span class="chip grey">${esc(TYPES[e.type] || e.type)}</span>
        ${state.view === "date" && e.domain ? `<span class="chip">${esc(DOMAINS[e.domain] || e.domain)}</span>` : ""}
        <span>${esc(e.date || "")}${e.time ? " à " + esc(e.time) : ""}</span>
        <span>· ${esc(e.author)}, ${esc(PROFESSIONS[e.profession] || e.profession)}</span>
        <span>· dictée ${esc(e.source_dictation)}</span>
      </div>
      <div class="entry-content">${esc(e.content)}${details ? ` <span class="muted">(${esc(details)})</span>` : ""}</div>
    </div>`;
}

function newestFirst(a, b) {
  const ka = `${a.date || ""} ${a.time || ""} ${a.id.slice(1).padStart(5, "0")}`;
  const kb = `${b.date || ""} ${b.time || ""} ${b.id.slice(1).padStart(5, "0")}`;
  return kb.localeCompare(ka);
}

function renderEntries() {
  const target = $("#entries");
  const entries = [...(state.patient?.entries || [])].sort(newestFirst);
  if (!entries.length) {
    target.innerHTML = `<div class="card empty" style="margin-top:14px">Aucune entrée pour l'instant. Commencez par une dictée.</div>`;
    return;
  }
  if (state.view === "date") {
    target.innerHTML = `<div class="entries" style="margin-top:14px">${entries.map(entryHtml).join("")}</div>`;
    return;
  }
  const groups = {};
  entries.forEach((e) => (groups[e.domain || "other"] ||= []).push(e));
  target.innerHTML = Object.keys(DOMAINS).filter((d) => groups[d]).map((d) => `
    <div class="group">
      <div class="group-title"><h2>${esc(DOMAINS[d])}</h2><span class="chip grey">${groups[d].length}</span></div>
      <div class="entries">${groups[d].map(entryHtml).join("")}</div>
    </div>`).join("");
}

// ---------- Ask ----------
$("#ask-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = $("#question").value.trim();
  const status = $("#ask-status");
  if (!question) {
    notice(status, "error", "Écrivez une question.");
    return;
  }
  const btn = $("#ask-btn");
  setLoading(btn, true, "Recherche…");
  notice(status, "", "");
  try {
    const r = await api(`/patients/${encodeURIComponent(state.patientId)}/ask`, { question });
    const item = document.createElement("div");
    item.className = "card qa-item";
    item.innerHTML = `
      <div class="q">${esc(question)}</div>
      <div class="a ${r.found ? "" : "not-found"}">${esc(r.answer)}</div>
      ${citationsHtml(r)}
      ${r.invalid_citations.length ? `<div class="notice error">Attention : citation introuvable (${esc(r.invalid_citations.join(", "))}). Vérifiez cette réponse.</div>` : ""}`;
    item.querySelectorAll("[data-ref]").forEach((chip) => chip.addEventListener("click", () => goToRef(chip.dataset.ref)));
    $("#qa").prepend(item);
    $("#question").value = "";
  } catch (err) {
    notice(status, "error", `La question a échoué : ${err.message}`);
  } finally {
    setLoading(btn, false, "Demander");
  }
});

// Citations: ids of the patient file (click: highlight in the file tab) and guideline refs (link to the PDF page).
function citationsHtml(r) {
  const sources = r.sources || {};
  const fileIds = r.citations.filter((c) => !(c in sources) && !r.invalid_citations.includes(c));
  const guides = r.citations.filter((c) => c in sources);
  const fileRow = fileIds.length ? `<div class="citations"><span class="muted small">Dossier :</span>
    ${fileIds.map((c) => `<button class="chip id" data-ref="${esc(c)}" title="Voir dans le dossier">${esc(c)}</button>`).join("")}</div>` : "";
  const guideRow = guides.length ? `<div class="citations"><span class="muted small">Recommandations :</span>
    ${guides.map((c) => {
      const s = sources[c];
      const label = `${String(s.title).replace(/^[A-Z]+\s*–\s*/, "")}, p. ${s.page}`;
      const url = typeof s.url === "string" && s.url.startsWith("https://") ? `${s.url}#page=${Number(s.page)}` : null;
      return url
        ? `<a class="chip guide" href="${esc(url)}" target="_blank" rel="noopener" title="${esc(s.title)}">${esc(label)} ↗</a>`
        : `<span class="chip guide" title="${esc(s.title)}">${esc(label)}</span>`;
    }).join("")}</div>` : "";
  return fileRow + guideRow;
}

// Open the file tab and highlight the cited entry, instruction or treatment.
function goToRef(ref) {
  showTab("file");
  const el = document.getElementById(`ref-${ref}`);
  if (!el) return;
  el.scrollIntoView({ behavior: "smooth", block: "center" });
  el.classList.add("flash");
  setTimeout(() => el.classList.remove("flash"), 2200);
}

// ---------- Navigation ----------
$("#back-btn").addEventListener("click", showHome);
$("#home-link").addEventListener("click", (e) => { e.preventDefault(); showHome(); });

showHome();