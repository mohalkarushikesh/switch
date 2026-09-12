"use strict";

// TaxPilot web console. Talks to the same FastAPI app that serves this page:
// POST /prepare (returns a draft, or awaiting_review), POST /resume (with
// corrections). Everything is relative-URL so it works on any host/port.

const $ = (id) => document.getElementById(id);
let threadId = null;
let lastResponse = null;
let lastBody = null;          // the last /prepare body, for "recompute under other regime"
let recomputeTarget = "old";  // the regime the recompute button will force
let pendingTab = null;        // a tab to open on the next render (deep link)
let llmConfigured = true;     // set from /health: is an API key configured?

// The pipeline stages, in order, with a friendly label. renderSteps marks the
// ones that appear in the run's trace as complete (a USWDS step indicator).
const STEPS = [
  ["guardrail_intake", "Intake"],
  ["extract", "Extract"],
  ["classify", "Classify"],
  ["research", "Research"],
  ["calculate", "Calculate"],
  ["audit", "Audit"],
  ["summarize", "Summarize"],
  ["review_gate", "Review"],
  ["report", "Report"],
  ["guardrail_output", "Check"],
];

// Sample shoeboxes. The first uses the server's bundled documents (documents:
// null -> reads DOCUMENTS_DIR); the rest are inline scenarios so the picker shows
// a range of outcomes: the marginal-relief zone, a senior citizen, and a return
// that trips the human-review gate.
const _profile = (age, regime) => ({
  filename: "00-profile.txt",
  text: `TAXPAYER PROFILE\nAge category: ${age}\nResidential status: resident\nTax regime: ${regime}`,
});
const _form16 = (salary, tds) => ({
  filename: "01-form16.txt",
  text: `FORM 16\nCertificate under Section 203\nEmployer: Acme Technologies Pvt Ltd\n` +
        `Employee PAN: ABCDE1234F\nGross salary: ${salary}\nTotal tax deducted: ${tds}`,
});

const EXAMPLES = [
  {
    label: "Salaried with home loan (₹14L)",
    description: "Form 16, interest, 80C, 80D, home-loan interest and Form 26AS. " +
      "The engine picks the new regime; a small refund.",
    server: true,
  },
  {
    label: "Young earner, no deductions (₹8L)",
    description: "Just a Form 16. Lands in the new-regime marginal-relief zone just above ₹7 lakh.",
    documents: [_profile("below 60", "auto"), _form16("8,00,000", "25,000")],
  },
  {
    label: "Senior citizen with 80D (₹8L pension)",
    description: "Higher basic exemption for a senior citizen, plus a Section 80D health cover.",
    documents: [
      _profile("senior citizen", "auto"),
      _form16("8,00,000", "60,000"),
      { filename: "02-80d.txt", text: "SECTION 80D HEALTH INSURANCE\nInsurer: Star Health\nPremium: 25,000" },
    ],
  },
  {
    label: "Salaried with HRA — needs review (₹12L)",
    description: "A rent receipt: HRA depends on the salary break-up, so it is sent to human review.",
    documents: [
      _profile("below 60", "auto"),
      _form16("12,00,000", "90,000"),
      { filename: "02-rent.txt", text: "RENT RECEIPT\nLandlord: R. Kumar\nRent paid: 2,40,000" },
    ],
  },
  {
    label: "Single IT professional (₹4.5 LPA)",
    description: "A single salaried professional at ₹4.5 LPA. After the ₹75,000 standard " +
      "deduction and the Section 87A rebate the tax is nil under both regimes.",
    documents: [_profile("below 60", "auto"), _form16("4,50,000", "0")],
  },
];

// ---------------------------------------------------------------- boot

document.addEventListener("DOMContentLoaded", () => {
  wireIntake();
  $("prepare").addEventListener("click", prepare);
  $("review-form").addEventListener("submit", onResume);
  $("btn-download").addEventListener("click", downloadDraft);
  $("btn-print").addEventListener("click", () => window.print());
  $("btn-recompute").addEventListener("click", recompute);
  $("theme-toggle").addEventListener("click", toggleTheme);
  $("use-llm").addEventListener("change", updateLlmHint);
  updateLlmHint();
  updateThemeIcon();
  wireAccordion("banner-toggle", "banner-content");
  wireTabs();
  loadHealth();
  // Shareable demo link: /#demo auto-prepares the selected example on load;
  // "/#demo:report" (etc.) also opens that tab once the result is ready.
  if (location.hash.startsWith("#demo")) {
    const tab = location.hash.split(":")[1];
    if (tab && TABS.includes(tab)) pendingTab = tab;
    prepare();
  }
});

const TABS = ["summary", "report", "sources", "audit", "guardrails", "trace"];

function wireTabs() {
  const buttons = TABS.map((n) => $(`tab-${n}-btn`));
  buttons.forEach((btn, i) => {
    btn.addEventListener("click", () => activateTab(TABS[i]));
    btn.addEventListener("keydown", (e) => {
      const d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (!d) return;
      e.preventDefault();
      const next = buttons[(i + d + buttons.length) % buttons.length];
      activateTab(TABS[buttons.indexOf(next)]);
      next.focus();
    });
  });
}

function activateTab(name) {
  for (const n of TABS) {
    const active = n === name;
    $(`tab-${n}-btn`).setAttribute("aria-selected", String(active));
    $(`tab-${n}-btn`).tabIndex = active ? 0 : -1;
    $(`tab-${n}`).classList.toggle("hidden", !active);
  }
}

function wireAccordion(btnId, panelId) {
  const btn = $(btnId);
  btn.addEventListener("click", () => {
    const nowHidden = $(panelId).classList.toggle("hidden");
    btn.setAttribute("aria-expanded", String(!nowHidden));
  });
}

function toggleTheme() {
  const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  try { localStorage.setItem("taxpilot-theme", next); } catch (e) { /* ignore */ }
  updateThemeIcon();
}

function updateThemeIcon() {
  const dark = document.documentElement.getAttribute("data-theme") === "dark";
  $("theme-toggle").textContent = dark ? "☀️" : "🌙";
}

function recompute() {
  if (!lastBody) return;
  run(() => postJson("/prepare", Object.assign({}, lastBody, { regime: recomputeTarget })));
}

async function loadHealth() {
  const status = $("status");
  try {
    const h = await fetchJson("/health");
    const feats = Object.entries(h.features).filter(([, on]) => on).map(([k]) => k).join(", ");
    status.innerHTML = `<span class="dot"></span>tax year ${esc(h.tax_year)} · ${esc(h.model)} · ${esc(feats)}`;
    status.className = "status ok";
    // When no API key is configured, default the run to deterministic-only so the
    // user isn't surprised by silent fallbacks; they can still flip it back on.
    llmConfigured = h.llm_configured !== false;
    if (!llmConfigured) $("use-llm").checked = false;
    updateLlmHint();
  } catch {
    status.innerHTML = `<span class="dot"></span>API unreachable`;
    status.className = "status bad";
  }
}

function updateLlmHint() {
  const on = $("use-llm").checked;
  const hint = $("llm-hint");
  if (!llmConfigured) {
    hint.textContent = on
      ? "No API key configured — AI stages will fall back to the deterministic engine."
      : "Deterministic engine only — no API key needed.";
    hint.className = on ? "llm-hint warn" : "llm-hint";
  } else {
    hint.textContent = on
      ? "AI enriches classification, deduction research and the written report."
      : "Deterministic engine only — faster and fully reproducible.";
    hint.className = "llm-hint";
  }
}

function wireIntake() {
  // Populate the example picker.
  const select = $("example");
  EXAMPLES.forEach((ex, i) => {
    const opt = document.createElement("option");
    opt.value = String(i);
    opt.textContent = ex.label;
    select.appendChild(opt);
  });
  const describe = () => { $("example-desc").textContent = EXAMPLES[+select.value].description; };
  select.addEventListener("change", describe);
  describe();

  // Toggle example vs upload panes.
  for (const radio of document.querySelectorAll('input[name="source"]')) {
    radio.addEventListener("change", (e) => {
      const upload = e.target.value === "upload";
      $("upload-area").classList.toggle("hidden", !upload);
      $("examples-area").classList.toggle("hidden", upload);
    });
  }
  $("files").addEventListener("change", (e) => {
    const list = $("file-list");
    list.innerHTML = "";
    for (const f of e.target.files) {
      const li = document.createElement("li");
      li.textContent = f.name;
      list.appendChild(li);
    }
  });
}

// ---------------------------------------------------------------- actions

async function prepare() {
  hide("intake-error");
  const source = document.querySelector('input[name="source"]:checked').value;
  let body = {};

  if (source === "upload") {
    const files = [...$("files").files];
    const docs = [];
    for (const f of files) {
      const text = (await f.text()).trim();
      if (text) docs.push({ filename: f.name, text });
    }
    if (!docs.length) {
      return showError("intake-error", "Add at least one non-empty text document, or use an example.");
    }
    body = { documents: docs };
  } else {
    const example = EXAMPLES[+$("example").value];
    body = example.server ? {} : { documents: example.documents };
  }

  body.use_llm = $("use-llm").checked;   // run with the model, or deterministic-only
  lastBody = body;   // remembered so "recompute under other regime" can re-post it
  await run(() => postJson("/prepare", body));
}

async function onResume(event) {
  event.preventDefault();
  if (!threadId) return;
  const corrections = [];
  const regime = $("fix-regime").value;
  const drop = $("fix-drop").value.trim();
  if (regime) corrections.push({ target: "regime", value: regime });
  if (drop) corrections.push({ target: "deduction_drop", value: drop });
  await run(() => postJson("/resume", { thread_id: threadId, corrections }));
}

async function run(request) {
  setBusy(true);
  try {
    const resp = await request();
    render(resp);
  } catch (err) {
    render(null, err);
  } finally {
    setBusy(false);
  }
}

// ---------------------------------------------------------------- rendering

function render(resp, error) {
  show("output");
  hide("placeholder");
  lastResponse = resp;

  if (error || !resp) {
    $("blocked").textContent = "Request failed: " + (error?.message || "unknown error");
    show("blocked");
    hide("review"); hide("regime-badge"); hide("regime-compare"); hide("btn-recompute");
    hide("ai-summary"); hide("det-note");
    ["steps", "metrics", "report", "citations", "audit-meter", "audit-flags",
     "guardrails", "trace"].forEach(clear);
    return;
  }

  threadId = resp.thread_id;

  const blocked = $("blocked");
  if (resp.blocked) {
    blocked.textContent = resp.block_message || "The return was blocked by a guardrail.";
    show("blocked");
  } else {
    hide("blocked");
  }

  activateTab(pendingTab || "summary");   // Summary by default; a deep link may override once
  pendingTab = null;
  renderSteps(resp.trace, resp.awaiting_review);
  renderReview(resp);
  renderRegimeBadge(resp.tax_return);
  renderRecompute(resp);
  renderAiSummary(resp);
  renderMetrics(resp.tax_return);
  renderRegimeCompare(resp.tax_return);
  $("report").innerHTML = resp.report ? mdToHtml(resp.report) : "<p>No report.</p>";
  renderCitations(resp.citations);
  renderAudit(resp.audit);
  renderGuardrails(resp.guardrails);
  renderTrace(resp.trace);
}

function renderSteps(trace, awaiting) {
  const done = new Set((trace || []).map((s) => s.node));
  const el = $("steps");
  el.innerHTML = STEPS.map(([node, label], i) => {
    let cls = "step";
    if (done.has(node)) cls += " done";
    // The gate is "current" while a run is paused for human review.
    if (awaiting && node === "review_gate") cls = "step current";
    return `<li class="${cls}"><span class="step-num">${i + 1}</span>` +
           `<span class="step-label">${esc(label)}</span></li>`;
  }).join("");
}

function renderRegimeBadge(ret) {
  const el = $("regime-badge");
  if (!ret) { hide("regime-badge"); return; }
  const gti = ret.gross_total_income || 0;
  const effective = gti > 0 ? ((ret.total_tax / gti) * 100).toFixed(1) : "0.0";
  el.innerHTML = `Computed under the <strong>${esc(ret.regime)}</strong> regime` +
    ` · effective rate ${effective}%`;
  show("regime-badge");
}

function renderRecompute(resp) {
  // Offer a one-click recompute of the same documents under the other regime.
  if (!resp.tax_return || resp.awaiting_review || !lastBody) { hide("btn-recompute"); return; }
  recomputeTarget = resp.tax_return.regime === "new" ? "old" : "new";
  $("btn-recompute").textContent = `Recompute under the ${recomputeTarget} regime`;
  show("btn-recompute");
}

function renderRegimeCompare(ret) {
  if (!ret) { hide("regime-compare"); return; }
  const chosen = ret.regime;                       // "old" | "new"
  const chosenTax = ret.total_tax;
  const otherTax = ret.alternative_regime_tax;
  const other = chosen === "new" ? "old" : "new";
  const saving = Math.max(0, otherTax - chosenTax);
  const cell = (name, tax, isChosen) =>
    `<div class="compare-cell ${isChosen ? "chosen" : ""}">` +
      `<div class="compare-name">${esc(name)} regime${isChosen ? " ✓" : ""}</div>` +
      `<div class="compare-tax">${money(tax)}</div>` +
      `<div class="compare-tag">${isChosen ? "chosen — lower tax" : "not chosen"}</div>` +
    `</div>`;
  $("compare-grid").innerHTML =
    cell(chosen, chosenTax, true) + cell(other, otherTax, false) +
    `<p class="compare-note">Choosing the ${esc(chosen)} regime saves ` +
    `<strong>${money(saving)}</strong> versus the ${esc(other)} regime.</p>`;
  show("regime-compare");
}

function downloadDraft() {
  if (!lastResponse) return;
  const blob = new Blob([JSON.stringify(lastResponse, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `taxpilot-draft-${lastResponse.tax_year || "return"}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function renderReview(resp) {
  const box = $("review");
  if (!resp.awaiting_review) { hide("review"); return; }
  const items = $("review-items");
  items.innerHTML = "";
  for (const it of resp.review_items) {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${esc(it.area)}</strong> — ${esc(it.reason)} ${esc(it.detail || "")}`;
    items.appendChild(li);
  }
  $("fix-regime").value = "";
  $("fix-drop").value = "";
  show("review");
}

function renderAiSummary(resp) {
  // The AI summary is the visible difference between an LLM run and a deterministic
  // one: show the model's text only when the LLM was used, and a plain note about
  // the deterministic engine otherwise.
  const usedLlm = resp.used_llm !== false;
  const text = (resp.llm_summary || "").trim();
  if (usedLlm && text) {
    $("ai-summary-text").textContent = text;
    show("ai-summary");
    hide("det-note");
  } else if (usedLlm) {
    // LLM run, but no summary came back (declined or dropped) — show nothing.
    hide("ai-summary");
    hide("det-note");
  } else {
    hide("ai-summary");
    show("det-note");
  }
}

function renderMetrics(ret) {
  const el = $("metrics");
  if (!ret) { el.innerHTML = ""; return; }
  const refund = ret.refund_or_due >= 0;
  el.innerHTML = [
    metric("Gross total income", money(ret.gross_total_income)),
    metric("Taxable income", money(ret.total_income)),
    metric("Total tax", money(ret.total_tax)),
    metric(refund ? "Refund" : "Balance payable", money(Math.abs(ret.refund_or_due)),
           refund ? "good" : "due"),
  ].join("");
}

function metric(label, value, cls = "") {
  return `<div class="metric ${cls}"><div class="label">${esc(label)}</div>` +
         `<div class="value">${esc(value)}</div></div>`;
}

function renderCitations(citations) {
  const el = $("citations");
  el.innerHTML = (citations && citations.length)
    ? citations.map((c) =>
        `<li><span class="rule">${esc(c.rule_id)}</span> — ${esc(label(c))}</li>`).join("")
    : "<li>None.</li>";
}

function label(c) {
  const where = c.source || c.rule_id;
  return c.section ? `${where} - ${c.section}` : where;
}

function renderAudit(audit) {
  const meter = $("audit-meter");
  const el = $("audit-flags");
  if (!audit) {
    meter.innerHTML = "";
    el.innerHTML = "<li>Not scored.</li>";
    return;
  }
  const pct = Math.max(0, Math.min(100, audit.score));
  // The meter fill carries severity by band; the score and band label sit above it,
  // so state never rests on color alone.
  meter.innerHTML =
    `<div class="meter-head">` +
      `<span class="meter-score">${audit.score}<small>/100</small></span>` +
      `<span class="risk-badge risk-${esc(audit.band)}">${esc(audit.band)} risk</span>` +
    `</div>` +
    `<div class="meter-track" role="meter" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100">` +
      `<div class="meter-fill ${esc(audit.band)}" style="width:${pct}%"></div>` +
    `</div>`;
  el.innerHTML = audit.flags.length
    ? audit.flags.map((f) =>
        `<li><span class="sev sev-${esc(f.severity)}">${esc(f.severity)}</span>` +
        `${esc(f.detail)} <span class="flag-detail">— ${esc(f.evidence || f.code)}</span></li>`).join("")
    : "<li>No red flags.</li>";
}

function renderGuardrails(guardrails) {
  const el = $("guardrails");
  const title = $("guardrails-title");
  if (!guardrails || !guardrails.length) {
    title.textContent = "Guardrails";
    el.innerHTML = "<span class='chip'>none run</span>";
    return;
  }
  const ran = guardrails.filter((g) => g.action !== "skip").length;
  title.innerHTML = `Guardrails <span class="ran-note">${ran} of ${guardrails.length} ran</span>`;
  el.innerHTML = guardrails.map((g) => {
    const cls = ["allow", "redact", "annotate", "block", "skip"].includes(g.action) ? g.action : "";
    return `<span class="chip ${cls}" title="${esc(g.detail)}"><span class="cdot"></span>` +
           `<span class="layer">${esc(g.layer)}</span> <span class="detail">${esc(g.detail)}</span></span>`;
  }).join("");
}

function renderTrace(trace) {
  const el = $("trace");
  el.innerHTML = (trace || []).map((s) =>
    `<tr><td class="node">${esc(s.node)}</td><td class="ms">${s.elapsed_ms} ms</td>` +
    `<td>${esc(s.detail || "")}</td></tr>`).join("");
}

// ---------------------------------------------------------------- helpers

function money(n) { return "₹" + Number(n).toLocaleString("en-IN"); }
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function show(id) { $(id).classList.remove("hidden"); }
function hide(id) { $(id).classList.add("hidden"); }
function clear(id) { const el = $(id); if (el) el.innerHTML = ""; }
function showError(id, msg) { const el = $(id); el.textContent = msg; el.classList.remove("hidden"); }
function setBusy(busy) {
  $("prepare").disabled = busy;
  $("loading").classList.toggle("hidden", !busy);
  if (busy) hide("placeholder");
}

async function fetchJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}
async function postJson(url, body) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || `${r.status} ${r.statusText}`);
  return data;
}

// Minimal Markdown -> HTML for the report (headings, bold, italic, code, lists,
// blockquotes, rules). Escapes first, so it is safe against injected HTML.
function mdToHtml(md) {
  // Italics only when the underscores sit at word boundaries, so snake_case tokens
  // like "deductions_at_cap" are never turned into "deductions<em>at</em>cap".
  const inline = (t) => esc(t)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^\w])_([^_]+?)_(?!\w)/g, "$1<em>$2</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>");
  let html = "", inList = false;
  const closeList = () => { if (inList) { html += "</ul>"; inList = false; } };
  for (const raw of md.split("\n")) {
    const line = raw.replace(/\s+$/, "");
    let m;
    if (/^---+\s*$/.test(line)) { closeList(); html += "<hr>"; }
    else if ((m = line.match(/^(#{1,4})\s+(.*)$/))) { closeList(); const l = m[1].length + 1; html += `<h${l}>${inline(m[2])}</h${l}>`; }
    else if ((m = line.match(/^\s*[-*]\s+(.*)$/))) { if (!inList) { html += "<ul>"; inList = true; } html += `<li>${inline(m[1])}</li>`; }
    else if ((m = line.match(/^>\s?(.*)$/))) { closeList(); html += `<blockquote>${inline(m[1])}</blockquote>`; }
    else if (line.trim() === "") { closeList(); }
    else { closeList(); html += `<p>${inline(line)}</p>`; }
  }
  closeList();
  return html;
}
