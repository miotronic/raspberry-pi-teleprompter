#!/usr/bin/env python3
"""
Teleprompter Web Interface
--------------------------
Lightweight Flask web server for managing teleprompter scripts.
Runs alongside the main teleprompter app on RPi Zero 2W.

Access via browser: http://teleprompter.local:5000

Features:
- Upload .txt script files via browser
- Delete scripts
- Preview script content
- No login required (local network only)
"""

import os
import json
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# =============================================================================
# CONFIGURATION
# =============================================================================
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), 'scripts')
ALLOWED_EXTENSIONS = {'txt'}
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB max per script file

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# =============================================================================
# SERVE FRONTEND
# =============================================================================

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Teleprompter</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0a0a0a;
    --surface: #111111;
    --border: #222222;
    --accent: #e8ff00;
    --accent-dim: rgba(232, 255, 0, 0.08);
    --text: #eeeeee;
    --muted: #555555;
    --red: #ff3b3b;
    --red-dim: rgba(255, 59, 59, 0.08);
  }

  html, body {
    height: 100%;
    background: var(--bg);
    color: var(--text);
    font-family: 'Space Mono', monospace;
    font-size: 14px;
  }

  body {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  /* HEADER */
  header {
    padding: 28px 32px 24px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: baseline;
    gap: 16px;
  }

  header h1 {
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: var(--accent);
  }

  header span {
    color: var(--muted);
    font-size: 12px;
  }

  /* MAIN LAYOUT */
  main {
    flex: 1;
    display: grid;
    grid-template-columns: 1fr 340px;
    gap: 0;
  }

  /* SCRIPTS PANEL */
  .scripts-panel {
    padding: 28px 32px;
    border-right: 1px solid var(--border);
  }

  .panel-title {
    font-family: 'Syne', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 20px;
  }

  .script-list {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .script-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border: 1px solid transparent;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s;
  }

  .script-item:hover {
    background: var(--accent-dim);
    border-color: var(--accent);
  }

  .script-item.active {
    background: var(--accent-dim);
    border-color: var(--accent);
  }

  .script-name {
    flex: 1;
    font-size: 13px;
    color: var(--text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .script-item.active .script-name {
    color: var(--accent);
  }

  .script-size {
    font-size: 11px;
    color: var(--muted);
    flex-shrink: 0;
  }

  .delete-btn {
    background: none;
    border: none;
    color: var(--muted);
    cursor: pointer;
    font-size: 16px;
    padding: 2px 4px;
    border-radius: 2px;
    transition: all 0.15s;
    flex-shrink: 0;
    line-height: 1;
  }

  .delete-btn:hover {
    color: var(--red);
    background: var(--red-dim);
  }

  .empty-state {
    padding: 40px 0;
    color: var(--muted);
    font-size: 13px;
    text-align: center;
  }

  /* SIDEBAR */
  .sidebar {
    padding: 28px 24px;
    display: flex;
    flex-direction: column;
    gap: 28px;
  }

  /* UPLOAD ZONE */
  .upload-zone {
    border: 1px dashed var(--border);
    border-radius: 6px;
    padding: 28px 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
  }

  .upload-zone:hover,
  .upload-zone.dragover {
    border-color: var(--accent);
    background: var(--accent-dim);
  }

  .upload-zone input[type="file"] {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
    width: 100%;
    height: 100%;
  }

  .upload-icon {
    font-size: 28px;
    margin-bottom: 10px;
    display: block;
  }

  .upload-label {
    font-family: 'Syne', sans-serif;
    font-size: 13px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 6px;
  }

  .upload-hint {
    font-size: 11px;
    color: var(--muted);
  }

  /* PREVIEW */
  .preview-box {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .preview-title {
    font-family: 'Syne', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
  }

  .preview-content {
    flex: 1;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 16px;
    font-size: 12px;
    line-height: 1.8;
    color: var(--text);
    white-space: pre-wrap;
    overflow-y: auto;
    max-height: 320px;
    min-height: 120px;
  }

  .preview-content .stage {
    color: #ff6b6b;
  }

  .preview-empty {
    color: var(--muted);
    font-style: italic;
  }

  /* TOAST */
  .toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: var(--surface);
    border: 1px solid var(--accent);
    color: var(--accent);
    padding: 12px 20px;
    border-radius: 4px;
    font-size: 13px;
    opacity: 0;
    transform: translateY(8px);
    transition: all 0.2s;
    pointer-events: none;
    z-index: 100;
  }

  .toast.error {
    border-color: var(--red);
    color: var(--red);
  }

  .toast.show {
    opacity: 1;
    transform: translateY(0);
  }

  /* STATUS BAR */
  footer {
    padding: 12px 32px;
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  .status-text {
    font-size: 11px;
    color: var(--muted);
  }

  .script-count {
    margin-left: auto;
    font-size: 11px;
    color: var(--muted);
  }
</style>
</head>
<body>

<header>
  <h1>TELEPROMPTER</h1>
  <span>script manager // teleprompter.local:5000</span>
</header>

<main>
  <div class="scripts-panel">
    <div class="panel-title">Scripts</div>
    <div class="script-list" id="scriptList">
      <div class="empty-state">Loading...</div>
    </div>
  </div>

  <div class="sidebar">
    <div>
      <div class="panel-title" style="margin-bottom:12px">Upload</div>
      <div class="upload-zone" id="uploadZone">
        <input type="file" id="fileInput" accept=".txt" multiple>
        <span class="upload-icon">↑</span>
        <div class="upload-label">Drop .txt files here</div>
        <div class="upload-hint">or click to browse</div>
      </div>
    </div>

    <div class="preview-box">
      <div class="preview-title">Preview</div>
      <div class="preview-content" id="previewContent">
        <span class="preview-empty">Select a script to preview</span>
      </div>
    </div>
  </div>
</main>

<footer>
  <div class="status-dot"></div>
  <div class="status-text">Connected to RPi</div>
  <div class="script-count" id="scriptCount">— scripts</div>
</footer>

<div class="toast" id="toast"></div>

<script>
  let activeScript = null;

  function showToast(msg, error = false) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'toast' + (error ? ' error' : '') + ' show';
    setTimeout(() => t.className = 'toast' + (error ? ' error' : ''), 2500);
  }

  function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    return (bytes / 1024).toFixed(1) + ' KB';
  }

  function renderPreview(text) {
    const lines = text.split('\\n');
    return lines.map(line => {
      const t = line.trim();
      if (t.startsWith('[') && t.endsWith(']')) {
        return '<span class="stage">' + escapeHtml(line) + '</span>';
      }
      return escapeHtml(line);
    }).join('\\n');
  }

  function escapeHtml(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  async function loadScripts() {
    const res = await fetch('/api/scripts');
    const data = await res.json();
    const list = document.getElementById('scriptList');
    const count = document.getElementById('scriptCount');

    count.textContent = data.scripts.length + ' script' + (data.scripts.length !== 1 ? 's' : '');

    if (data.scripts.length === 0) {
      list.innerHTML = '<div class="empty-state">No scripts yet.<br>Upload a .txt file to get started.</div>';
      return;
    }

    list.innerHTML = data.scripts.map(s => `
      <div class="script-item ${activeScript === s.name ? 'active' : ''}"
           onclick="selectScript('${s.name}')">
        <span class="script-name">${escapeHtml(s.name.replace('.txt',''))}</span>
        <span class="script-size">${formatSize(s.size)}</span>
        <button class="delete-btn" onclick="deleteScript(event,'${s.name}')" title="Delete">×</button>
      </div>
    `).join('');
  }

  async function selectScript(name) {
    activeScript = name;
    await loadScripts();
    const res = await fetch('/api/scripts/' + encodeURIComponent(name));
    const data = await res.json();
    document.getElementById('previewContent').innerHTML = renderPreview(data.content);
  }

  async function deleteScript(e, name) {
    e.stopPropagation();
    if (!confirm('Delete "' + name.replace('.txt','') + '"?')) return;
    const res = await fetch('/api/scripts/' + encodeURIComponent(name), { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      if (activeScript === name) {
        activeScript = null;
        document.getElementById('previewContent').innerHTML = '<span class="preview-empty">Select a script to preview</span>';
      }
      showToast('Deleted ' + name.replace('.txt',''));
      loadScripts();
    } else {
      showToast('Error: ' + data.error, true);
    }
  }

  async function uploadFiles(files) {
    for (const file of files) {
      if (!file.name.endsWith('.txt')) {
        showToast('Only .txt files allowed', true);
        continue;
      }
      const form = new FormData();
      form.append('file', file);
      const res = await fetch('/api/upload', { method: 'POST', body: form });
      const data = await res.json();
      if (data.success) {
        showToast('Uploaded ' + file.name.replace('.txt',''));
      } else {
        showToast('Error: ' + data.error, true);
      }
    }
    loadScripts();
  }

  // File input
  document.getElementById('fileInput').addEventListener('change', e => {
    uploadFiles(Array.from(e.target.files));
    e.target.value = '';
  });

  // Drag and drop
  const zone = document.getElementById('uploadZone');
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragover');
    uploadFiles(Array.from(e.dataTransfer.files));
  });

  loadScripts();
</script>
</body>
</html>'''


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route('/api/scripts')
def list_scripts():
    """Return list of all scripts with metadata."""
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    scripts = []
    for f in sorted(os.listdir(SCRIPTS_DIR)):
        if f.endswith('.txt'):
            path = os.path.join(SCRIPTS_DIR, f)
            scripts.append({
                'name': f,
                'size': os.path.getsize(path)
            })
    return jsonify({'scripts': scripts})


@app.route('/api/scripts/<filename>')
def get_script(filename):
    """Return content of a specific script."""
    filename = secure_filename(filename)
    path = os.path.join(SCRIPTS_DIR, filename)
    if not os.path.exists(path):
        return jsonify({'error': 'Not found'}), 404
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return jsonify({'name': filename, 'content': content})


@app.route('/api/scripts/<filename>', methods=['DELETE'])
def delete_script(filename):
    """Delete a script file."""
    filename = secure_filename(filename)
    path = os.path.join(SCRIPTS_DIR, filename)
    if not os.path.exists(path):
        return jsonify({'success': False, 'error': 'Not found'}), 404
    os.remove(path)
    return jsonify({'success': True})


@app.route('/api/upload', methods=['POST'])
def upload_script():
    """Upload a new script file."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No filename'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Only .txt files allowed'}), 400

    filename = secure_filename(file.filename)
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    file.save(os.path.join(SCRIPTS_DIR, filename))

    return jsonify({'success': True, 'filename': filename})


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    print("Teleprompter web interface running at http://teleprompter.local:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
