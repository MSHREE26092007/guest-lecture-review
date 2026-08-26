"""HTML Dashboard for Guest Lecture Document Review Agent."""

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Guest Lecture Document Review Agent</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --border-color: #334155;
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --accent: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background-color: var(--bg-color); color: var(--text-main); min-height: 100vh; padding: 2rem 1rem; }
        .container { max-width: 1100px; margin: 0 auto; }
        
        header { text-align: center; margin-bottom: 2.5rem; }
        header h1 { font-size: 2.2rem; font-weight: 700; background: linear-gradient(135deg, #818cf8, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        header p { color: var(--text-muted); margin-top: 0.5rem; font-size: 1.05rem; }

        .layout { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
        @media (max-width: 850px) { .layout { grid-template-columns: 1fr; } }

        .card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 1rem; padding: 1.5rem; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3); }
        .card h2 { font-size: 1.3rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }

        .dropzone { border: 2px dashed var(--border-color); border-radius: 0.75rem; padding: 2.5rem 1rem; text-align: center; cursor: pointer; transition: all 0.2s ease; background: rgba(15, 23, 42, 0.4); }
        .dropzone:hover, .dropzone.dragover { border-color: var(--primary); background: rgba(99, 102, 241, 0.05); }
        .dropzone input { display: none; }
        .dropzone-icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
        .file-name { margin-top: 0.75rem; font-weight: 600; color: #a5b4fc; word-break: break-all; }

        .btn { width: 100%; margin-top: 1.25rem; padding: 0.85rem; border: none; border-radius: 0.5rem; background: var(--primary); color: white; font-weight: 600; font-size: 1rem; cursor: pointer; transition: background 0.2s ease; }
        .btn:hover { background: var(--primary-hover); }
        .btn:disabled { background: #475569; cursor: not-allowed; opacity: 0.7; }

        .module-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem; margin-top: 1rem; }
        .module-item { background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border-color); border-radius: 0.5rem; padding: 0.75rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; }
        .status-badge { font-size: 0.8rem; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-weight: 600; }
        .status-pending { background: #334155; color: #94a3b8; }
        .status-running { background: #1e3a8a; color: #93c5fd; }
        .status-done { background: #064e3b; color: #6ee7b7; }
        .status-failed { background: #7f1d1d; color: #fca5a5; }

        .score-box { background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(16, 185, 129, 0.15)); border: 1px solid var(--primary); border-radius: 0.75rem; padding: 1.25rem; text-align: center; margin-bottom: 1.25rem; }
        .score-value { font-size: 2.2rem; font-weight: 700; color: #818cf8; }
        .score-grade { font-size: 1.1rem; color: #34d399; font-weight: 600; margin-top: 0.25rem; }

        .section-title { font-size: 1rem; font-weight: 600; margin: 1.25rem 0 0.5rem 0; color: #cbd5e1; border-bottom: 1px solid var(--border-color); padding-bottom: 0.3rem; }
        .list-item { font-size: 0.9rem; padding: 0.4rem 0; color: var(--text-muted); display: flex; align-items: flex-start; gap: 0.4rem; }
        .list-item strong { color: var(--text-main); }

        .alert { padding: 0.75rem; border-radius: 0.5rem; margin-top: 0.75rem; font-size: 0.9rem; }
        .alert-warning { background: rgba(245, 158, 11, 0.1); border: 1px solid var(--warning); color: #fde68a; }
        .alert-error { background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger); color: #fca5a5; }
        .alert-info { background: rgba(99, 102, 241, 0.1); border: 1px solid var(--primary); color: #c7d2fe; }

        .hidden { display: none; }
        .spinner { border: 3px solid rgba(255,255,255,0.1); border-radius: 50%; border-top: 3px solid white; width: 1.2rem; height: 1.2rem; animation: spin 1s linear infinite; display: inline-block; vertical-align: middle; margin-right: 0.5rem; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📄 Guest Lecture Document Review Agent</h1>
            <p>Upload a university report (.docx or .pdf) to analyze formatting, completeness, grammar, and policy compliance.</p>
        </header>

        <div class="layout">
            <!-- Left Column: File Upload & Controls -->
            <div class="card">
                <h2>📤 Upload Report</h2>
                <div class="dropzone" id="dropzone" onclick="document.getElementById('fileInput').click()">
                    <div class="dropzone-icon">📁</div>
                    <p>Click or drag & drop file here</p>
                    <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.4rem;">Supported formats: .DOCX, .PDF</p>
                    <input type="file" id="fileInput" accept=".docx,.pdf" onchange="handleFileSelect(event)">
                    <div class="file-name" id="fileName"></div>
                </div>

                <button class="btn" id="submitBtn" onclick="uploadAndReview()" disabled>Run Review Pipeline</button>
                <div id="statusMessage" style="margin-top: 1rem; font-size: 0.9rem; color: var(--text-muted); text-align: center;"></div>
            </div>

            <!-- Right Column: Results & Scorecard -->
            <div class="card">
                <h2>🔎 Live Pipeline & Results</h2>
                
                <div id="moduleGrid" class="module-grid">
                    <div class="module-item"><span>Template</span><span id="mod-template" class="status-badge status-pending">Pending</span></div>
                    <div class="module-item"><span>Formatting</span><span id="mod-formatting" class="status-badge status-pending">Pending</span></div>
                    <div class="module-item"><span>Completeness</span><span id="mod-completeness" class="status-badge status-pending">Pending</span></div>
                    <div class="module-item"><span>Semantic</span><span id="mod-semantic" class="status-badge status-pending">Pending</span></div>
                    <div class="module-item"><span>Grammar</span><span id="mod-grammar" class="status-badge status-pending">Pending</span></div>
                    <div class="module-item"><span>Policy</span><span id="mod-policy" class="status-badge status-pending">Pending</span></div>
                </div>

                <div id="resultContainer" class="hidden" style="margin-top: 1.5rem;">
                    <div class="score-box">
                        <div class="score-value" id="overallScore">0.0 / 100.0</div>
                        <div class="score-grade" id="overallGrade">Grade: -</div>
                    </div>

                    <div class="section-title">Criteria Breakdown</div>
                    <div id="criteriaList"></div>

                    <div id="missingSection" class="hidden">
                        <div class="alert alert-warning">
                            <strong>⚠️ Missing Required Items:</strong>
                            <div id="missingList" style="margin-top: 0.3rem;"></div>
                        </div>
                    </div>

                    <div id="formattingSection" class="hidden">
                        <div class="alert alert-error">
                            <strong>🛠️ Formatting Errors:</strong>
                            <div id="formattingList" style="margin-top: 0.3rem;"></div>
                        </div>
                    </div>

                    <div id="suggestionsSection" class="hidden">
                        <div class="alert alert-info">
                            <strong>💡 Improvement Suggestions:</strong>
                            <div id="suggestionsList" style="margin-top: 0.3rem;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedFile = null;
        let activeSubmissionId = null;

        function handleFileSelect(evt) {
            const files = evt.target.files || evt.dataTransfer.files;
            if (files.length > 0) {
                selectedFile = files[0];
                document.getElementById('fileName').innerText = `Selected: ${selectedFile.name} (${(selectedFile.size/1024).toFixed(1)} KB)`;
                document.getElementById('submitBtn').disabled = false;
            }
        }

        const dropzone = document.getElementById('dropzone');
        dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
        dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            handleFileSelect(e);
        });

        function updateModuleStatus(module, state) {
            const el = document.getElementById(`mod-${module}`);
            if (!el) return;
            el.className = 'status-badge ' + (
                state === 'done' ? 'status-done' :
                state === 'running' ? 'status-running' :
                state === 'failed' ? 'status-failed' : 'status-pending'
            );
            el.innerText = state ? state.toUpperCase() : 'PENDING';
        }

        async function uploadAndReview() {
            if (!selectedFile) return;
            const btn = document.getElementById('submitBtn');
            const msg = document.getElementById('statusMessage');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span>Uploading file...';

            const formData = new FormData();
            formData.append('file', selectedFile);

            try {
                // 1. Upload
                const uploadRes = await fetch('/upload', { method: 'POST', body: formData });
                if (!uploadRes.ok) throw new Error('File upload failed');
                const uploadData = await uploadRes.json();
                activeSubmissionId = uploadData.submission_id;

                msg.innerText = `Uploaded successfully. Starting review pipeline...`;
                btn.innerHTML = '<span class="spinner"></span>Running analysis...';

                // Set running status for modules
                ['template', 'formatting', 'completeness', 'semantic', 'grammar', 'policy'].forEach(m => updateModuleStatus(m, 'running'));

                // 2. Trigger Review
                const reviewRes = await fetch(`/review/${activeSubmissionId}`, { method: 'POST' });
                if (!reviewRes.ok) throw new Error('Review execution failed');
                
                // 3. Fetch Final Report
                const reportRes = await fetch(`/report/${activeSubmissionId}`);
                if (!reportRes.ok) throw new Error('Failed to retrieve final report');
                const reportData = await reportRes.json();

                // 4. Update UI
                ['template', 'formatting', 'completeness', 'semantic', 'grammar', 'policy'].forEach(m => updateModuleStatus(m, 'done'));
                displayReport(reportData);
                
                btn.innerHTML = 'Run Review Pipeline';
                btn.disabled = false;
                msg.innerText = 'Review complete!';
            } catch (err) {
                console.error(err);
                msg.innerText = `Error: ${err.message}`;
                btn.innerHTML = 'Run Review Pipeline';
                btn.disabled = false;
            }
        }

        function displayReport(r) {
            document.getElementById('resultContainer').classList.remove('hidden');
            
            const pct = ((r.overall_score / r.overall_max) * 100).toFixed(0);
            document.getElementById('overallScore').innerText = `${r.overall_score.toFixed(1)} / ${r.overall_max.toFixed(1)} (${pct}%)`;
            document.getElementById('overallGrade').innerText = `Grade: ${r.grade}`;

            // Criteria
            const critEl = document.getElementById('criteriaList');
            critEl.innerHTML = r.criteria.map(c => `
                <div class="list-item">
                    <span>📌</span>
                    <div>
                        <strong>${c.label}</strong>: ${c.score.toFixed(1)} / ${c.max_score.toFixed(1)} 
                        <span style="font-size: 0.8rem; color: #94a3b8;">(${c.mode})</span>
                        ${c.detail ? `<div style="font-size: 0.8rem; color: #cbd5e1;">${c.detail}</div>` : ''}
                    </div>
                </div>
            `).join('');

            // Missing Items
            const missSec = document.getElementById('missingSection');
            if (r.missing_items && r.missing_items.length > 0) {
                missSec.classList.remove('hidden');
                document.getElementById('missingList').innerHTML = r.missing_items.map(m => `<div>• ${m}</div>`).join('');
            } else { missSec.classList.add('hidden'); }

            // Formatting Errors
            const fmtSec = document.getElementById('formattingSection');
            if (r.formatting_errors && r.formatting_errors.length > 0) {
                fmtSec.classList.remove('hidden');
                document.getElementById('formattingList').innerHTML = r.formatting_errors.map(e => `<div>• ${e.label}: expected "${e.expected || '-'}", got "${e.actual || '-'}"</div>`).join('');
            } else { fmtSec.classList.add('hidden'); }

            // Suggestions
            const sugSec = document.getElementById('suggestionsSection');
            if (r.suggestions && r.suggestions.length > 0) {
                sugSec.classList.remove('hidden');
                document.getElementById('suggestionsList').innerHTML = r.suggestions.map(s => `<div><strong>${s.title}</strong>: ${s.detail}</div>`).join('');
            } else { sugSec.classList.add('hidden'); }
        }
    </script>
</body>
</html>
"""
