/* ═══════════════════════════════════════════════════════════════
   ContradictPrompt v2.0 — Application Logic
   Clean SVG Iconography, First-Class NVIDIA NIM Integration,
   and Robust Error Handling across all Research Workflows
   ═══════════════════════════════════════════════════════════════ */

// ─── SVG Icon Library (Zero Emojis) ───────────────────────────
const ICONS = {
  check: `<svg class="icon-svg" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
  warning: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
  impossible: `<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line></svg>`,
  help: `<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
  info: `<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`,
  bolt: `<svg class="icon-svg" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>`,
  edit: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>`,
  document: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>`,
  save: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>`,
  download: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>`,
  message: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>`,
  play: `<svg class="icon-svg" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>`,
  wrench: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path></svg>`,
  chart: `<svg class="icon-svg" viewBox="0 0 24 24"><line x1="12" y1="20" x2="12" y2="10"></line><line x1="18" y1="20" x2="18" y2="4"></line><line x1="6" y1="20" x2="6" y2="16"></line></svg>`,
  clipboard: `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>`,
  cpu: `<svg class="icon-svg" viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>`
};

const API = '';

// ─── Application State ─────────────────────────────────────────
const state = {
  activePage: 'home',
  analysis: null,
  validated: null,
  repairs: [],
  selectedRepair: -1,
  cases: [],
  reviews: [],
  evaluations: [],
  saveHistory: false,
  lastResponse: null,
  nimStatus: {
    active: true,
    provider: 'nvidia_nim',
    model: 'nvidia/nemotron-3.5-super-vl-120b-a12b',
    latency_ms: null
  }
};

// ─── Sample Prompts ───────────────────────────────────────────
const SAMPLES = {
  numerical: 'Write exactly 100 words, but use fewer than 80 words.',
  formatting: 'Return the response as valid JSON only, but format it as an unformatted bullet list.',
  temporal: 'Complete the task before beginning the preparation.',
  compatible: 'Write a concise technical summary of quantum computing in approximately 50 words.',
  underspecified: 'Summarize the attached document in three sentences.',
};

// ─── Navigation ───────────────────────────────────────────────
function navigateTo(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const targetPage = document.getElementById(`page-${pageId}`);
  const targetNav = document.getElementById(`nav-${pageId}`);

  if (targetPage) targetPage.classList.add('active');
  if (targetNav) targetNav.classList.add('active');

  state.activePage = pageId;
  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Page-specific initializers
  if (pageId === 'repair') updateRepairPage();
  if (pageId === 'generator') updateGeneratorPage();
  if (pageId === 'evaluation') loadEvaluationResults();

  // Close mobile sidebar if open
  document.getElementById('sidebar')?.classList.remove('open');
}

// ─── Mobile Sidebar Toggle ────────────────────────────────────
document.getElementById('mobileToggle')?.addEventListener('click', () => {
  document.getElementById('sidebar')?.classList.toggle('open');
});

// Sidebar nav click handlers
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', () => {
    navigateTo(item.dataset.page);
  });
});

// ─── History Toggle ───────────────────────────────────────────
document.getElementById('historyToggle')?.addEventListener('click', () => {
  state.saveHistory = !state.saveHistory;
  document.getElementById('historySwitch')?.classList.toggle('active', state.saveHistory);
  showToast(state.saveHistory ? 'Local history logging enabled' : 'Local history logging disabled', 'info');
});

// ─── Toast Notifications ─────────────────────────────────────
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const iconMap = {
    success: ICONS.check,
    error: ICONS.impossible,
    info: ICONS.info,
    warning: ICONS.warning
  };

  toast.innerHTML = `
    <span class="toast-icon">${iconMap[type] || ICONS.info}</span>
    <span class="toast-msg">${escapeHtml(message)}</span>
    <button class="toast-close" onclick="this.parentElement.remove()" aria-label="Close">×</button>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    if (toast.parentElement) {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(60px)';
      setTimeout(() => toast.remove(), 300);
    }
  }, duration);
}

// ─── Utilities ───────────────────────────────────────────────
function escapeHtml(text) {
  if (text === null || text === undefined) return '';
  const div = document.createElement('div');
  div.textContent = String(text);
  return div.innerHTML;
}

function getLabelBadge(label) {
  const classes = {
    'Compatible': 'badge-compatible',
    'Partially conflicting': 'badge-partial',
    'Fully impossible': 'badge-impossible',
    'Underspecified': 'badge-underspecified',
  };
  const iconMap = {
    'Compatible': ICONS.check,
    'Partially conflicting': ICONS.warning,
    'Fully impossible': ICONS.impossible,
    'Underspecified': ICONS.help,
  };
  return `<span class="badge ${classes[label] || ''}">${iconMap[label] || ''} ${escapeHtml(label)}</span>`;
}

function getHighlightedText(result) {
  const ids = new Set();
  (result.conflicts || []).forEach(c => (c.instruction_ids || []).forEach(id => ids.add(id)));

  const spans = [];
  (result.instructions || []).forEach(i => {
    if (ids.has(i.id)) spans.push([i.start, i.end]);
  });
  spans.sort((a, b) => a[0] - b[0]);

  // Merge overlapping spans
  const merged = [];
  for (const [a, b] of spans) {
    if (merged.length && a <= merged[merged.length - 1][1]) {
      merged[merged.length - 1][1] = Math.max(b, merged[merged.length - 1][1]);
    } else {
      merged.push([a, b]);
    }
  }

  let html = '';
  let pos = 0;
  for (const [a, b] of merged) {
    html += escapeHtml(result.original.slice(pos, a));
    html += '<mark>' + escapeHtml(result.original.slice(a, b)) + '</mark>';
    pos = b;
  }
  html += escapeHtml(result.original.slice(pos));
  return html;
}

async function apiCall(endpoint, data = null, method = 'POST') {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (data) options.body = JSON.stringify(data);

  const response = await fetch(`${API}${endpoint}`, options);
  const json = await response.json();

  if (!response.ok) {
    throw new Error(json.error || `Server error ${response.status}`);
  }
  return json;
}

// ─── NVIDIA NIM Diagnostics & Connection Test ─────────────────
async function testNimConnection() {
  const btn = document.getElementById('testNimBtn');
  const latencyEl = document.getElementById('nimLatency');
  const dot = document.getElementById('nimStatusDot');

  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Testing…';
  }

  try {
    const res = await apiCall('/api/llm/test', {}, 'POST');
    if (res.success) {
      if (dot) dot.className = 'status-dot online';
      if (latencyEl) {
        latencyEl.innerHTML = `<span style="color: var(--accent-emerald);">Online &bull; ${res.latency_ms}ms</span>`;
      }
      showToast(`NVIDIA NIM connected (${res.latency_ms}ms): "${res.response}"`, 'success', 5000);
    }
  } catch (err) {
    if (dot) dot.className = 'status-dot offline';
    if (latencyEl) {
      latencyEl.innerHTML = `<span style="color: var(--accent-rose);">Error &bull; Check API Key</span>`;
    }
    showToast(`NVIDIA NIM Connection Error: ${err.message}`, 'error', 6000);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Test Ping';
    }
  }
}

// ─── Load Sample Prompts & 100-Prompt Benchmark Explorer ───────
const USER_CRITICAL_PROMPTS = {
  coral: "An underwater coral reef teeming with colorful tropical fish, but the entire scene is bone-dry and covered in desert dust",
  eulogy: "Write a deeply heartbreaking eulogy for a funeral, but make the tone incredibly cheerful, upbeat, and celebratory like a lottery win.",
  monologue: "Write a highly descriptive, 500-word monologue for a character who refuses to speak a single word or communicate in any way."
};

function loadUserCritical(key) {
  const p = USER_CRITICAL_PROMPTS[key];
  if (!p) return;
  document.getElementById('analyzerInput').value = p;
  const modeSelect = document.getElementById('detectorMode');
  if (modeSelect) modeSelect.value = 'hybrid';
  clearAnalysis();
  showToast(`Loaded critical test prompt. Detector mode set to Hybrid (Rules + NVIDIA NIM).`, 'info');
}

async function loadBenchmarkPrompts() {
  try {
    const res = await apiCall('/api/benchmark/prompts', null, 'GET');
    state.benchmarkPrompts = res.prompts || [];
    populateBenchmarkPromptSelect(state.benchmarkPrompts);
  } catch (err) {
    console.error('Failed to load benchmark prompts:', err);
  }
}

function populateBenchmarkPromptSelect(prompts) {
  const select = document.getElementById('benchmarkPromptSelect');
  if (!select) return;
  select.innerHTML = '<option value="">-- Choose a benchmark prompt to test (' + prompts.length + ' available) --</option>';
  prompts.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.id;
    opt.textContent = `[${p.id}] ${p.prompt.length > 70 ? p.prompt.slice(0, 68) + '…' : p.prompt}`;
    select.appendChild(opt);
  });
}

function onBenchmarkCategoryChange() {
  const cat = document.getElementById('benchmarkCategorySelect').value;
  const filtered = cat === 'all' 
    ? state.benchmarkPrompts 
    : state.benchmarkPrompts.filter(p => p.category_id === cat);
  populateBenchmarkPromptSelect(filtered);
  const hint = document.getElementById('benchmarkHint');
  if (hint) hint.style.display = 'none';
}

function onBenchmarkPromptSelect() {
  const selId = document.getElementById('benchmarkPromptSelect').value;
  const hint = document.getElementById('benchmarkHint');
  if (!hint) return;
  const item = state.benchmarkPrompts.find(p => p.id === selId);
  if (!item) {
    hint.style.display = 'none';
    return;
  }
  hint.innerHTML = `<strong>${escapeHtml(item.contradiction_type)}</strong> &bull; Expected: <em>${escapeHtml(item.expected_label)}</em> &bull; ${escapeHtml(item.explanation)}`;
  hint.style.display = 'block';
}

function loadSelectedBenchmarkPrompt() {
  const selId = document.getElementById('benchmarkPromptSelect').value;
  const item = state.benchmarkPrompts.find(p => p.id === selId);
  if (!item) {
    showToast('Please select a benchmark prompt from the dropdown first.', 'info');
    return;
  }
  document.getElementById('analyzerInput').value = item.prompt;
  const modeSelect = document.getElementById('detectorMode');
  if (modeSelect) modeSelect.value = 'hybrid';
  clearAnalysis();
  showToast(`Loaded ${item.id}: ${item.contradiction_type}. Ready for Hybrid analysis!`, 'success');
}

function loadSample(type) {
  document.getElementById('analyzerInput').value = SAMPLES[type] || '';
  clearAnalysis();
}

function loadExample() {
  navigateTo('analyzer');
  document.getElementById('analyzerInput').value = SAMPLES.numerical;
}

// ─── Analyze Prompt ──────────────────────────────────────────
async function analyzePrompt() {
  const prompt = document.getElementById('analyzerInput').value.trim();
  if (!prompt) {
    showToast('Please enter a prompt to analyze.', 'error');
    return;
  }

  const btn = document.getElementById('analyzeBtn');
  btn.classList.add('loading');
  btn.disabled = true;

  try {
    const mode = document.getElementById('detectorMode').value;
    const result = await apiCall('/api/analyze', {
      prompt,
      mode,
      save_history: state.saveHistory,
    });

    state.analysis = result;
    state.validated = result.label === 'Compatible' ? result : null;
    state.repairs = [];
    state.selectedRepair = -1;

    renderAnalysisResult(result);
    showToast(`Classification: ${result.label}`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
    document.getElementById('analysisResult').classList.add('hidden');
  } finally {
    btn.classList.remove('loading');
    btn.disabled = false;
  }
}

function clearAnalysis() {
  state.analysis = null;
  state.validated = null;
  state.repairs = [];
  document.getElementById('analysisResult').classList.add('hidden');
}

function renderAnalysisResult(result) {
  const container = document.getElementById('analysisResult');
  container.classList.remove('hidden');

  let html = '<div class="result-panel">';

  // Header
  html += `<div class="glass-card">`;
  html += `<div class="result-header">`;
  html += `<h3 style="font-size: 1.1rem; font-weight: 600;">Analysis Result</h3>`;
  html += getLabelBadge(result.label);
  html += `</div>`;

  // Explanation
  html += `<div class="result-explanation">${escapeHtml(result.explanation)}</div>`;

  // Highlighted prompt
  html += `<div class="highlighted-prompt">${getHighlightedText(result)}</div>`;

  // Conflicts
  if (result.conflicts && result.conflicts.length > 0) {
    html += `<h4 style="font-size: 0.9rem; font-weight: 600; margin-bottom: var(--space-sm); color: var(--text-primary);">Detected Conflicts</h4>`;
    for (const c of result.conflicts) {
      html += `<div class="conflict-item">
        <span class="conflict-icon">${ICONS.bolt}</span>
        <div>
          <div class="conflict-meta">
            <span class="conflict-tag">${escapeHtml(c.kind)}</span>
            <span class="conflict-tag" style="background: ${c.severity === 'hard' ? 'rgba(244,63,94,0.15)' : 'rgba(245,158,11,0.15)'}; color: ${c.severity === 'hard' ? '#fb7185' : '#fbbf24'}">
              ${c.severity}
            </span>
            <span class="conflict-tag" style="background: rgba(99,102,241,0.1); color: var(--text-accent);">
              ${(c.instruction_ids || []).join(', ')}
            </span>
          </div>
          <div class="conflict-text">${escapeHtml(c.explanation)}</div>
        </div>
      </div>`;
    }
  }

  // Clarification questions
  if (result.clarification_questions && result.clarification_questions.length > 0) {
    html += `<h4 style="font-size: 0.9rem; font-weight: 600; margin: var(--space-lg) 0 var(--space-sm); color: var(--text-primary);">Clarification Needed</h4>`;
    for (const q of result.clarification_questions) {
      html += `<div class="clarification-item">
        <span class="clarification-icon">${ICONS.message}</span>
        <span class="clarification-text">${escapeHtml(q)}</span>
      </div>`;
    }
  }

  // Warnings
  if (result.warnings && result.warnings.length > 0) {
    html += `<div style="margin-top: var(--space-lg)">`;
    for (const w of result.warnings) {
      html += `<div class="warning-item">${ICONS.warning} <span>${escapeHtml(w)}</span></div>`;
    }
    html += `</div>`;
  }

  // Instructions table
  if (result.instructions && result.instructions.length > 0) {
    html += `
    <div class="expandable open" style="margin-top: var(--space-lg)">
      <div class="expandable-header" onclick="this.parentElement.classList.toggle('open')">
        <span>Extracted Instructions (${result.instructions.length})</span>
        <span class="expandable-arrow">▼</span>
      </div>
      <div class="expandable-body">
        <div class="expandable-content" style="overflow-x: auto;">
          <table class="instructions-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Kind</th>
                <th>Scope</th>
                <th>Key</th>
                <th>Value</th>
                <th>Bounds</th>
                <th>Text</th>
              </tr>
            </thead>
            <tbody>`;
    for (const i of result.instructions) {
      html += `<tr>
        <td class="mono">${escapeHtml(i.id)}</td>
        <td><span class="badge" style="font-size:0.68rem; padding: 0.15rem 0.5rem; background: rgba(99,102,241,0.1); color: var(--text-accent); border: 1px solid rgba(99,102,241,0.15);">${escapeHtml(i.kind)}</span></td>
        <td class="mono">${escapeHtml(i.scope)}</td>
        <td class="mono">${escapeHtml(i.key)}</td>
        <td>${escapeHtml(i.value || '—')}</td>
        <td class="mono">${i.lower !== null || i.upper !== null ? `[${i.lower ?? '∞'}, ${i.upper ?? '∞'}]` : '—'}</td>
        <td style="max-width: 250px; word-break: break-word;">${escapeHtml(i.text)}</td>
      </tr>`;
    }
    html += `</tbody></table></div></div></div>`;
  }

  // Status bar
  html += `<div class="status-bar" style="margin-top: var(--space-lg);">
    <span>${result.latency_ms?.toFixed(1) ?? '—'} ms</span>
    <span>·</span>
    <span>${result.usage?.calls ?? 0} model calls</span>
    <span>·</span>
    <span>Semantic Verified: ${result.semantic_checked ? 'Yes' : 'Offline'}</span>
    <span>·</span>
    <span>Mode: ${result.mode}</span>
  </div>`;

  // Action buttons
  html += `<div style="display: flex; gap: var(--space-md); margin-top: var(--space-lg); flex-wrap: wrap;">`;
  if (result.label !== 'Compatible') {
    html += `<button class="btn btn-primary" onclick="navigateTo('repair')">
      ${ICONS.wrench} <span style="margin-left: 6px;">Go to Repair</span>
    </button>`;
  } else {
    html += `<button class="btn btn-success" onclick="navigateTo('generator')">
      ${ICONS.bolt} <span style="margin-left: 6px;">Generate Response</span>
    </button>`;
  }
  html += `<button class="btn btn-secondary" onclick="exportAnalysis()">
    ${ICONS.download} <span style="margin-left: 6px;">Export JSON</span>
  </button>`;
  html += `</div>`;

  html += `</div></div>`;
  container.innerHTML = html;
}

function exportAnalysis() {
  if (!state.analysis) return;
  const blob = new Blob([JSON.stringify(state.analysis, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'contradiction_analysis.json';
  a.click();
  URL.revokeObjectURL(url);
  showToast('Analysis exported to JSON', 'success');
}

// ─── Repair Page ─────────────────────────────────────────────
async function updateRepairPage() {
  const container = document.getElementById('repairContent');

  if (!state.analysis) {
    container.innerHTML = `<div class="info-banner">
      <span class="icon">${ICONS.info}</span>
      <span>Analyze a prompt first in the Prompt Analyzer to see repair suggestions here.</span>
    </div>`;
    return;
  }

  // Get repair suggestions if not already loaded
  if (state.repairs.length === 0 && (state.analysis.conflicts || []).length > 0) {
    try {
      state.repairs = await apiCall('/api/repair/suggestions', {
        analysis: state.analysis,
      });
    } catch (err) {
      showToast('Failed to get repair suggestions: ' + err.message, 'error');
    }
  }

  let html = '';

  // Original prompt
  html += `<div class="glass-card">
    <div class="card-title" style="margin-bottom: var(--space-md)">
      <span class="icon">${ICONS.document}</span> Original Prompt
    </div>
    <div class="code-block">${escapeHtml(state.analysis.original)}</div>
  </div>`;

  // Clarification questions
  if (state.analysis.clarification_questions && state.analysis.clarification_questions.length > 0) {
    for (const q of state.analysis.clarification_questions) {
      html += `<div class="clarification-item" style="margin-bottom: var(--space-md);">
        <span class="clarification-icon">${ICONS.message}</span>
        <span class="clarification-text">${escapeHtml(q)} (Incorporate this clarification in the edited prompt below).</span>
      </div>`;
    }
  }

  // Repair options
  if (state.repairs.length > 0) {
    html += `<div class="glass-card">
      <div class="card-title" style="margin-bottom: var(--space-lg)">
        <span class="icon">${ICONS.wrench}</span> Suggested Corrections
      </div>`;

    for (let i = 0; i < state.repairs.length; i++) {
      const r = state.repairs[i];
      const selected = i === state.selectedRepair;
      html += `<div class="repair-option ${selected ? 'selected' : ''}" onclick="selectRepair(${i})">
        <div class="repair-radio"></div>
        <div style="flex: 1;">
          <div class="repair-description">${escapeHtml(r.description)}</div>
          <div class="repair-preview">${escapeHtml(r.prompt)}</div>
        </div>
      </div>`;
    }

    html += `<button class="btn btn-secondary btn-sm" style="margin-top: var(--space-md);" onclick="loadSelectedRepair()">
      ${ICONS.clipboard} <span style="margin-left: 6px;">Load into Editor</span>
    </button>`;
    html += `</div>`;
  }

  // Editor
  const editValue = state.selectedRepair >= 0 && state.repairs[state.selectedRepair]
    ? state.repairs[state.selectedRepair].prompt
    : state.analysis.original;

  html += `<div class="glass-card">
    <div class="card-title" style="margin-bottom: var(--space-md)">
      <span class="icon">${ICONS.edit}</span> Edited Prompt
    </div>
    <div class="input-group">
      <textarea class="textarea" id="repairEditor" style="min-height: 140px;">${escapeHtml(editValue)}</textarea>
    </div>

    <div class="checkbox-group" id="approvalCheckbox" onclick="toggleApproval()">
      <div class="custom-checkbox"></div>
      <span>I approve this exact edited prompt for revalidation</span>
    </div>

    <button class="btn btn-primary" id="revalidateBtn" onclick="revalidatePrompt()">
      ${ICONS.check} <span style="margin-left: 6px;">Approve &amp; Revalidate</span>
    </button>
  </div>`;

  // Recheck result placeholder
  html += `<div id="recheckResult"></div>`;

  container.innerHTML = html;
}

function selectRepair(index) {
  state.selectedRepair = index;
  document.querySelectorAll('.repair-option').forEach((el, i) => {
    el.classList.toggle('selected', i === index);
  });
}

function loadSelectedRepair() {
  if (state.selectedRepair >= 0 && state.repairs[state.selectedRepair]) {
    const editor = document.getElementById('repairEditor');
    if (editor) {
      editor.value = state.repairs[state.selectedRepair].prompt;
      showToast('Correction loaded into editor', 'info');
    }
  }
}

let repairApproved = false;
function toggleApproval() {
  repairApproved = !repairApproved;
  document.getElementById('approvalCheckbox').classList.toggle('checked', repairApproved);
}

async function revalidatePrompt() {
  const editor = document.getElementById('repairEditor');
  if (!editor) return;

  const prompt = editor.value.trim();
  if (!prompt) {
    showToast('Please enter a prompt.', 'error');
    return;
  }

  const btn = document.getElementById('revalidateBtn');
  btn.classList.add('loading');
  btn.disabled = true;

  try {
    const mode = document.getElementById('detectorMode').value;
    const result = await apiCall('/api/repair/revalidate', {
      prompt,
      approved: repairApproved,
      mode,
      save_history: state.saveHistory,
    });

    if (result.label === 'Compatible') {
      state.validated = result;
      showToast('Prompt validated as Compatible! You can now generate a response.', 'success');
    } else {
      state.validated = null;
      showToast(`Revalidation result: ${result.label}`, 'info');
    }

    // Render the recheck result
    const container = document.getElementById('recheckResult');
    container.innerHTML = '';

    const wrapper = document.createElement('div');
    wrapper.className = 'glass-card result-panel';
    wrapper.style.marginTop = 'var(--space-lg)';

    let inner = `<div class="result-header">
      <h3 style="font-size: 1.05rem; font-weight: 600;">Revalidation Result</h3>
      ${getLabelBadge(result.label)}
    </div>`;
    inner += `<div class="result-explanation">${escapeHtml(result.explanation)}</div>`;
    inner += `<div class="highlighted-prompt">${getHighlightedText(result)}</div>`;

    if (result.label === 'Compatible') {
      inner += `<button class="btn btn-success" onclick="navigateTo('generator')" style="margin-top: var(--space-md);">
        ${ICONS.bolt} <span style="margin-left: 6px;">Go to Response Generator</span>
      </button>`;
    }

    wrapper.innerHTML = inner;
    container.appendChild(wrapper);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.classList.remove('loading');
    btn.disabled = false;
  }
}

// ─── Generator Page ──────────────────────────────────────────
function updateGeneratorPage() {
  const container = document.getElementById('generatorContent');

  if (!state.validated) {
    container.innerHTML = `<div class="info-banner">
      <span class="icon">${ICONS.info}</span>
      <span>Analyze a compatible prompt or approve and revalidate a correction first.</span>
    </div>`;
    return;
  }

  let html = `<div class="glass-card">
    <div class="card-title" style="margin-bottom: var(--space-md)">
      <span class="icon">${ICONS.check}</span> Validated Prompt
    </div>
    <div class="code-block">${escapeHtml(state.validated.original)}</div>

    <div class="warning-item" style="margin-top: var(--space-lg);">
      ${ICONS.warning} <span>Prompt validation and answer quality are separate. Offline validation checks only recognized patterns.</span>
    </div>

    <div class="checkbox-group" id="genApprovalCheckbox" onclick="toggleGenApproval()" style="margin-top: var(--space-lg);">
      <div class="custom-checkbox"></div>
      <span>I approve sending this exact prompt to the configured NVIDIA NIM model</span>
    </div>

    <button class="btn btn-primary" id="generateBtn" onclick="generateResponse()">
      ${ICONS.bolt} <span style="margin-left: 6px;">Generate Response</span>
    </button>
  </div>`;

  html += `<div id="generatedResponse"></div>`;
  container.innerHTML = html;
}

let genApproved = false;
function toggleGenApproval() {
  genApproved = !genApproved;
  document.getElementById('genApprovalCheckbox').classList.toggle('checked', genApproved);
}

async function generateResponse() {
  if (!state.validated) return;

  const btn = document.getElementById('generateBtn');
  btn.classList.add('loading');
  btn.disabled = true;

  try {
    const result = await apiCall('/api/generate', {
      prompt: state.validated.original,
      approved: genApproved,
      analysis: state.validated,
    });

    const container = document.getElementById('generatedResponse');
    let html = `<div class="glass-card result-panel">
      <div class="card-header">
        <div class="card-title" style="margin-bottom: 0;">
          <span class="icon">${ICONS.message}</span> Generated Response
        </div>
        <span class="badge" style="background: rgba(16,185,129,0.15); color: var(--accent-emerald); border: 1px solid rgba(16,185,129,0.25);">
          ${escapeHtml(result.model || 'NVIDIA NIM')}
        </span>
      </div>
      <div class="response-content" style="margin-top: var(--space-md);">${escapeHtml(result.answer)}</div>`;

    // Usage & details
    html += `<div class="expandable open" style="margin-top: var(--space-lg);">
      <div class="expandable-header" onclick="this.parentElement.classList.toggle('open')">
        <span>Execution &amp; Verification Details</span>
        <span class="expandable-arrow">▼</span>
      </div>
      <div class="expandable-body">
        <div class="expandable-content">
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: var(--space-md); margin-bottom: var(--space-md);">
            <div class="metric-card">
              <div class="metric-value">${result.usage?.latency_ms ? (result.usage.latency_ms / 1000).toFixed(2) + 's' : '—'}</div>
              <div class="metric-label">Latency</div>
            </div>
            <div class="metric-card">
              <div class="metric-value">${result.usage?.input_tokens ?? '—'}</div>
              <div class="metric-label">Prompt Tokens</div>
            </div>
            <div class="metric-card">
              <div class="metric-value">${result.usage?.output_tokens ?? '—'}</div>
              <div class="metric-label">Completion Tokens</div>
            </div>
          </div>
          <h4 style="margin-top: var(--space-md); font-size: 0.9rem; color: var(--text-primary);">Automated Satisfaction Check</h4>
          <div class="code-block" style="margin-top: var(--space-sm);">${escapeHtml(JSON.stringify(result.satisfaction, null, 2))}</div>
        </div>
      </div>
    </div>`;

    // Download button
    html += `<div style="margin-top: var(--space-lg);">
      <button class="btn btn-secondary btn-sm" onclick="downloadResponse()">
        ${ICONS.download} <span style="margin-left: 6px;">Download Response</span>
      </button>
    </div>`;

    html += `</div>`;
    container.innerHTML = html;

    state.lastResponse = result.answer;
    showToast('Response generated successfully via NVIDIA NIM', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.classList.remove('loading');
    btn.disabled = false;
  }
}

function downloadResponse() {
  if (!state.lastResponse) return;
  const blob = new Blob([state.lastResponse], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'generated_response.txt';
  a.click();
  URL.revokeObjectURL(url);
}

// ─── Evaluation Page ─────────────────────────────────────────
function switchEvalTab(tabName) {
  document.querySelectorAll('#evalTabs .tab').forEach(el => {
    el.classList.toggle('active', el.dataset.tab === tabName);
  });
  document.querySelectorAll('.tab-panel').forEach(el => {
    el.classList.toggle('active', el.id === `tab-${tabName}`);
  });

  if (tabName === 'review') loadCases();
}

async function loadEvaluationResults() {
  const container = document.getElementById('evalResults');

  try {
    const evaluations = await apiCall('/api/evaluation/results', null, 'GET');

    if (evaluations.length === 0) {
      container.innerHTML = `<div class="info-banner">
        <span class="icon">${ICONS.info}</span>
        <span>No evaluation results found. Run: <code>python -m scripts.evaluate --split dev</code></span>
      </div>
      <button class="btn btn-primary" onclick="runEvaluation()">
        ${ICONS.play} <span style="margin-left: 6px;">Run Development Evaluation</span>
      </button>`;
      return;
    }

    let html = '';

    for (const ev of evaluations) {
      const m = ev.metrics;

      html += `<div class="glass-card">
        <div class="card-header">
          <div class="card-title">
            <span class="icon">${ICONS.chart}</span> ${escapeHtml(ev.name)}
          </div>
          <span class="badge" style="background: rgba(99,102,241,0.1); color: var(--text-accent); border: 1px solid rgba(99,102,241,0.15);">${m.n} cases</span>
        </div>`;

      // Metrics cards
      html += `<div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-value">${(m.accuracy * 100).toFixed(1)}%</div>
          <div class="metric-label">Accuracy</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">${(m.macro_f1 * 100).toFixed(1)}%</div>
          <div class="metric-label">Macro F1</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">${(m.conflict_f1 * 100).toFixed(1)}%</div>
          <div class="metric-label">Conflict F1</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">${m.latency_median_ms?.toFixed(2) ?? '—'}</div>
          <div class="metric-label">Median Latency (ms)</div>
        </div>
      </div>`;

      // Classification report
      if (m.classification_report) {
        html += `<div class="expandable" style="margin-bottom: var(--space-md);">
          <div class="expandable-header" onclick="this.parentElement.classList.toggle('open')">
            <span>Classification Report</span>
            <span class="expandable-arrow">▼</span>
          </div>
          <div class="expandable-body">
            <div class="expandable-content" style="overflow-x: auto;">
              <table class="instructions-table">
                <thead><tr><th>Label</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr></thead>
                <tbody>`;

        for (const [label, stats] of Object.entries(m.classification_report)) {
          if (typeof stats === 'object' && stats.precision !== undefined) {
            html += `<tr>
              <td>${escapeHtml(label)}</td>
              <td class="mono">${stats.precision.toFixed(3)}</td>
              <td class="mono">${stats.recall.toFixed(3)}</td>
              <td class="mono">${stats['f1-score'].toFixed(3)}</td>
              <td class="mono">${stats.support}</td>
            </tr>`;
          }
        }

        html += `</tbody></table></div></div></div>`;
      }

      // Images
      if (ev.images) {
        for (const [name, url] of Object.entries(ev.images)) {
          html += `<div class="expandable">
            <div class="expandable-header" onclick="this.parentElement.classList.toggle('open')">
              <span>${escapeHtml(name.replace('.png', '').replace(/_/g, ' '))}</span>
              <span class="expandable-arrow">▼</span>
            </div>
            <div class="expandable-body">
              <div class="expandable-content">
                <img src="${url}" alt="${escapeHtml(name)}" class="eval-image" />
              </div>
            </div>
          </div>`;
        }
      }

      // Full metrics JSON
      html += `<div class="expandable">
        <div class="expandable-header" onclick="this.parentElement.classList.toggle('open')">
          <span>Full Metrics JSON</span>
          <span class="expandable-arrow">▼</span>
        </div>
        <div class="expandable-body">
          <div class="expandable-content">
            <div class="code-block">${escapeHtml(JSON.stringify(m, null, 2))}</div>
          </div>
        </div>
      </div>`;

      html += `</div>`;
    }

    // Fetch additional research evaluation artifacts
    let baselines = null;
    let adversarial = null;
    let failures = null;

    try { baselines = await apiCall('/api/evaluation/baselines', null, 'GET'); } catch(e){}
    try { adversarial = await apiCall('/api/evaluation/adversarial', null, 'GET'); } catch(e){}
    try { failures = await apiCall('/api/evaluation/failures', null, 'GET'); } catch(e){}

    // ─── 1. Research Baselines Comparison Table (A through F) ───
    if (baselines) {
      html += `<div class="glass-card" style="margin-bottom: var(--space-xl);">
        <div class="card-header">
          <div class="card-title">
            <span class="icon">${ICONS.chart}</span> Research Baselines &amp; Model Customization Comparison (A through F)
          </div>
          <span class="badge" style="background: rgba(16,185,129,0.1); color: var(--success); border: 1px solid rgba(16,185,129,0.2);">1,000-Prompt Benchmark</span>
        </div>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: var(--space-md);">
          Standardized evaluation across the 6 primary detector configurations on identical held-out test splits.
        </p>
        <div style="overflow-x: auto;">
          <table class="instructions-table">
            <thead>
              <tr>
                <th>Configuration</th>
                <th>Accuracy</th>
                <th>Macro-F1</th>
                <th>Binary F1</th>
                <th>Mean Latency</th>
                <th>Tokens (In/Out)</th>
              </tr>
            </thead>
            <tbody>`;
      for (const [key, b] of Object.entries(baselines)) {
        html += `<tr>
          <td style="font-weight: 500; color: var(--text-primary);">${escapeHtml(b.model_name)}</td>
          <td class="mono">${(b.accuracy * 100).toFixed(1)}%</td>
          <td class="mono">${(b.macro_f1 * 100).toFixed(1)}%</td>
          <td class="mono">${(b.binary_f1 * 100).toFixed(1)}%</td>
          <td class="mono">${b.mean_latency_ms.toFixed(1)} ms</td>
          <td class="mono">${Math.round(b.mean_input_tokens)} / ${Math.round(b.mean_output_tokens)}</td>
        </tr>`;
      }
      html += `</tbody></table></div></div>`;
    }

    // ─── 2. Adversarial Challenge Groups Breakdown (A through P) ───
    if (adversarial && adversarial.groups_breakdown) {
      html += `<div class="glass-card" style="margin-bottom: var(--space-xl);">
        <div class="card-header">
          <div class="card-title">
            <span class="icon">${ICONS.impossible}</span> 16 Adversarial Challenge Groups &amp; Complexity Tiers (A through P)
          </div>
          <span class="badge" style="background: rgba(99,102,241,0.1); color: var(--text-accent); border: 1px solid rgba(99,102,241,0.15);">${(adversarial.overall_metrics.classification.accuracy * 100).toFixed(1)}% Overall Acc</span>
        </div>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: var(--space-md);">
          Performance breakdown by adversarial challenge category, evaluating robustness on traps, long-distance dependencies, and edge cases.
        </p>
        <div style="overflow-x: auto;">
          <table class="instructions-table">
            <thead>
              <tr>
                <th>Group</th>
                <th>Category Name</th>
                <th>Total Cases</th>
                <th>Correct</th>
                <th>Accuracy</th>
                <th>Mean Latency</th>
              </tr>
            </thead>
            <tbody>`;
      for (const [grpCode, g] of Object.entries(adversarial.groups_breakdown)) {
        const accPct = (g.accuracy * 100).toFixed(1);
        const color = g.accuracy >= 0.8 ? 'var(--success)' : (g.accuracy >= 0.5 ? 'var(--warning)' : 'var(--danger)');
        html += `<tr>
          <td class="mono" style="font-weight: 700; color: var(--text-accent);">Group ${escapeHtml(grpCode)}</td>
          <td>${escapeHtml(g.group_name)}</td>
          <td class="mono">${g.total_cases}</td>
          <td class="mono">${g.correct}</td>
          <td class="mono" style="font-weight: 600; color: ${color};">${accPct}%</td>
          <td class="mono">${g.mean_latency_ms} ms</td>
        </tr>`;
      }
      html += `</tbody></table></div></div>`;
    }

    // ─── 3. Failure Registry Summary ───
    if (failures) {
      html += `<div class="glass-card" style="margin-bottom: var(--space-xl);">
        <div class="card-header">
          <div class="card-title">
            <span class="icon">${ICONS.warning}</span> Failure Registry &amp; Root Cause Taxonomy (Section 16)
          </div>
          <a class="btn btn-secondary btn-xs" href="/api/evaluation/failures" download="failure_registry.json">
            ${ICONS.download} Export JSON Registry
          </a>
        </div>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: var(--space-md);">
          Systematic diagnosis of all ${failures.total_failures} misclassified cases categorized by structural failure mechanism.
        </p>
        <div class="categories-grid" style="margin-top: var(--space-md)">`;
      for (const [catName, count] of Object.entries(failures.failures_by_category)) {
        if (count > 0) {
          html += `<div class="category-card">
            <div class="category-name" style="color: var(--warning);">${escapeHtml(catName)}</div>
            <div class="category-desc"><strong>${count}</strong> cases diagnosed under this root cause.</div>
          </div>`;
        }
      }
      html += `</div></div>`;
    }

    // Run button
    html += `<button class="btn btn-primary" onclick="runEvaluation()" style="margin-top: var(--space-md);">
      ${ICONS.play} <span style="margin-left: 6px;">Re-run Development Evaluation</span>
    </button>`;

    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div class="info-banner">
      <span class="icon">${ICONS.warning}</span>
      <span>Failed to load results: ${escapeHtml(err.message)}</span>
    </div>`;
  }
}

async function runEvaluation() {
  showToast('Running development evaluation…', 'info');
  try {
    const result = await apiCall('/api/evaluation/run', { split: 'dev' });
    showToast('Evaluation completed successfully', 'success');
    loadEvaluationResults();
  } catch (err) {
    showToast('Evaluation failed: ' + err.message, 'error');
  }
}

// ─── Case Review ─────────────────────────────────────────────
async function loadCases() {
  const split = document.getElementById('reviewSplit').value;

  try {
    state.cases = await apiCall(`/api/cases?split=${split}`, null, 'GET');

    if (state.cases.length === 0) {
      document.getElementById('caseSelector').classList.add('hidden');
      document.getElementById('caseDisplay').classList.add('hidden');
      document.getElementById('reviewForm').classList.add('hidden');
      return;
    }

    const select = document.getElementById('caseSelect');
    select.innerHTML = state.cases.map(c =>
      `<option value="${escapeHtml(c.id)}">${escapeHtml(c.id)}</option>`
    ).join('');

    document.getElementById('caseSelector').classList.remove('hidden');
    displayCase();
  } catch (err) {
    showToast('Failed to load cases: ' + err.message, 'error');
  }
}

function displayCase() {
  const caseId = document.getElementById('caseSelect').value;
  const c = state.cases.find(x => x.id === caseId);
  if (!c) return;

  const display = document.getElementById('caseDisplay');
  display.classList.remove('hidden');
  display.innerHTML = `
    <div style="margin: var(--space-lg) 0;">
      <div class="code-block">${escapeHtml(c.prompt)}</div>
      <p style="font-size: 0.78rem; color: var(--text-muted); margin-top: var(--space-sm);">
        Assign your label independently before inspecting template rationale.
      </p>
      <div class="expandable" style="margin-top: var(--space-md);">
        <div class="expandable-header" onclick="this.parentElement.classList.toggle('open')">
          <span>Template Label &amp; Rationale (inspect after independent labeling)</span>
          <span class="expandable-arrow">▼</span>
        </div>
        <div class="expandable-body">
          <div class="expandable-content">
            <div class="code-block">${escapeHtml(JSON.stringify(c, null, 2))}</div>
          </div>
        </div>
      </div>
    </div>`;

  document.getElementById('reviewForm').classList.remove('hidden');
}

async function submitReview() {
  const caseId = document.getElementById('caseSelect').value;
  const reviewer = document.getElementById('reviewerName').value.trim();
  const label = document.getElementById('reviewLabel').value;
  const reason = document.getElementById('reviewReason').value.trim();
  const corrected = document.getElementById('reviewCorrected').value.trim();
  const stage = document.getElementById('reviewStage').value;

  if (!reviewer || !reason) {
    showToast('Reviewer name and rationale are required.', 'error');
    return;
  }

  try {
    await apiCall('/api/reviews', {
      case_id: caseId,
      reviewer,
      label,
      reason,
      corrected_prompt: corrected,
      stage,
    });
    showToast('Review saved successfully', 'success');
    document.getElementById('reviewReason').value = '';
    document.getElementById('reviewCorrected').value = '';
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ─── Health & NIM Status Check ───────────────────────────────
async function checkHealth() {
  try {
    const health = await apiCall('/api/health', null, 'GET');
    const dot = document.getElementById('statusDot');
    const text = document.getElementById('statusText');

    if (dot) dot.className = `status-dot ${health.llm_available ? 'online' : 'offline'}`;
    if (text) {
      text.textContent = health.llm_available
        ? `${health.provider}: ${health.model}`
        : 'Offline (rules only)';
    }

    // Update NIM status card
    const nimDot = document.getElementById('nimStatusDot');
    const nimModel = document.getElementById('nimModelName');
    if (nimDot && health.nvidia_nim_configured) {
      nimDot.className = 'status-dot online';
    }
    if (nimModel && health.model) {
      const parts = health.model.split('/');
      nimModel.textContent = parts[parts.length - 1] || health.model;
    }
  } catch {
    const dot = document.getElementById('statusDot');
    const text = document.getElementById('statusText');
    if (dot) dot.className = 'status-dot offline';
    if (text) text.textContent = 'Server unavailable';
  }
}

// ─── Initialization ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  checkHealth();
  loadBenchmarkPrompts();
  setInterval(checkHealth, 30000);
});
