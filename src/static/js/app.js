/* Main JS for Medicine AI System
    Enhances UI with drag-and-drop upload, AJAX APIs, and dynamic updates.
*/
(function () {
    const log = (...args) => console.debug('[MedicineAI]', ...args);

    // Loading overlay
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
    document.addEventListener('DOMContentLoaded', () => document.body.appendChild(overlay));
    const showLoading = () => overlay.classList.add('show');
    const hideLoading = () => overlay.classList.remove('show');

    async function fetchJSON(url, options) {
        const resp = await fetch(url, options);
        const data = await resp.json().catch(() => ({ success: false, error: 'Invalid JSON' }));
        if (!resp.ok) throw new Error(data.error || ('HTTP ' + resp.status));
        return data;
    }

    // Severity mapping based on description keywords
    function severityFromDesc(desc) {
        const d = (desc || '').toLowerCase();
        if (d.includes('contraindicat') || d.includes('bleeding') || d.includes('severe')) return 'major';
        if (d.includes('potential') || d.includes('monitor') || d.includes('caution')) return 'moderate';
        return 'minor';
    }

    function renderSeverityBadge(sev) {
        const cls = sev === 'major' ? 'severity-major' : sev === 'moderate' ? 'severity-moderate' : 'severity-minor';
        const label = sev.charAt(0).toUpperCase() + sev.slice(1);
        return `<span class="severity-badge ${cls}">${label}</span>`;
    }

    // Drag-and-drop upload
    function initDropzone() {
        const dz = document.getElementById('pill-dropzone');
        const fileInput = document.getElementById('pill-file');
        const resultBox = document.getElementById('identify-result');
        if (!dz || !fileInput) return;

        const prevent = e => { e.preventDefault(); e.stopPropagation(); };
        ['dragenter', 'dragover'].forEach(ev => dz.addEventListener(ev, e => { prevent(e); dz.classList.add('dragover'); }));
        ;['dragleave', 'drop'].forEach(ev => dz.addEventListener(ev, e => { prevent(e); dz.classList.remove('dragover'); }));
        dz.addEventListener('drop', e => {
            const files = e.dataTransfer.files;
            if (files && files[0]) handleUpload(files[0]);
        });
        dz.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', () => { if (fileInput.files[0]) handleUpload(fileInput.files[0]); });

        async function handleUpload(file) {
            try {
                showLoading();
                const fd = new FormData();
                fd.append('image', file);
                const data = await fetchJSON('/api/identify-pill', { method: 'POST', body: fd });
                const conf = (data.confidence * 100).toFixed(2) + '%';
                resultBox.innerHTML = `<div class="alert alert-info mb-2">Prediction: <strong>${data.pill_id}</strong> (Confidence: ${conf})</div>`;
            } catch (err) {
                console.error(err);
                alert('Identify failed: ' + err.message);
            } finally { hideLoading(); }
        }
    }

    // Real-time search
    function initDrugSearch() {
        const input = document.getElementById('drug-search');
        const list = document.getElementById('drug-results');
        if (!input || !list) return;
        let t;
        input.addEventListener('input', () => {
            clearTimeout(t);
            const q = input.value.trim();
            if (!q) { list.innerHTML = ''; return; }
            t = setTimeout(async () => {
                try {
                    const data = await fetchJSON('/api/search-drugs?q=' + encodeURIComponent(q));
                    list.innerHTML = data.results.map(r => `<li class="list-group-item d-flex justify-content-between align-items-center">
                     <span>${r.name} <small class="text-muted">(${r.imprint})</small></span>
                     <button class="btn btn-sm btn-outline-primary" data-add="${r.name}" data-dose="${r.strength}">Add</button>
                  </li>`).join('');
                } catch (err) { list.innerHTML = '<li class="list-group-item text-danger">Error: ' + err.message + '</li>'; }
            }, 300);
        });
        list.addEventListener('click', async (e) => {
            const btn = e.target.closest('button[data-add]');
            if (!btn) return;
            try {
                await fetchJSON('/api/add-medication', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: btn.dataset.add, dose: btn.dataset.dose }) });
                location.reload();
            } catch (err) { alert('Add failed: ' + err.message); }
        });
    }

    // Medications list with remove
    function initMedications() {
        const list = document.getElementById('med-list');
        if (!list) return;
        list.addEventListener('click', async (e) => {
            const btn = e.target.closest('button[data-index]');
            if (!btn) return;
            try {
                await fetchJSON('/api/remove-medication?index=' + encodeURIComponent(btn.dataset.index));
                location.reload();
            } catch (err) { alert('Remove failed: ' + err.message); }
        });
    }

    // Session interactions button
    function initInteractions() {
        const btn = document.getElementById('btn-check-interactions');
        const box = document.getElementById('interaction-results');
        if (!btn || !box) return;
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                showLoading();
                const data = await fetchJSON('/api/check-interactions');
                const items = Object.entries(data.interactions || {}).map(([pair, desc]) => {
                    const sev = severityFromDesc(desc);
                    return `<li class="list-group-item d-flex justify-content-between align-items-center">
                  <span><strong>${pair}</strong>: ${desc}</span>
                  ${renderSeverityBadge(sev)}
               </li>`;
                }).join('');
                box.innerHTML = `<ul class="list-group">${items || '<li class="list-group-item">No interactions found.</li>'}</ul>`;
            } catch (err) {
                box.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
            } finally { hideLoading(); }
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        initDropzone();
        initDrugSearch();
        initMedications();
        initInteractions();
        log('UI initialized');
    });
})();
