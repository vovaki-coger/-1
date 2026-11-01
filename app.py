import os
import time
import uuid
from datetime import datetime, timedelta
from flask import Flask, send_from_directory, jsonify, request, abort

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(BASE_DIR, "files")
os.makedirs(FILES_DIR, exist_ok=True)

# Track upload times for auto-deletion
file_times = {}  # filename -> datetime

DELETE_AFTER_MINUTES = 20


def cleanup_old_files():
    """Background thread: delete files older than DELETE_AFTER_MINUTES"""
    while True:
        time.sleep(60)  # check every minute
        now = datetime.now()
        to_delete = []
        for filename, upload_time in list(file_times.items()):
            if now - upload_time > timedelta(minutes=DELETE_AFTER_MINUTES):
                filepath = os.path.join(FILES_DIR, filename)
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                        print(f"[CLEANUP] Deleted {filename}")
                    except Exception as e:
                        print(f"[CLEANUP] Error deleting {filename}: {e}")
                to_delete.append(filename)
        for filename in to_delete:
            file_times.pop(filename, None)


# Start cleanup thread
import threading
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()


HTML_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JustMC File Host</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; }
        .card { background: #1e293b; padding: 2rem; border-radius: 12px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5); max-width: 500px; width: 100%; border: 1px solid #334155; }
        h1 { color: #38bdf8; margin-bottom: 1rem; font-size: 1.5rem; }
        p { color: #94a3b8; margin-bottom: 1.5rem; font-size: 0.9rem; }
        .drop-zone { border: 2px dashed #475569; border-radius: 8px; padding: 2rem; text-align: center; cursor: pointer; transition: all 0.2s; background: #0f172a; }
        .drop-zone:hover { border-color: #38bdf8; background: #1e293b; }
        .drop-zone.dragover { border-color: #38bdf8; background: #1e293b; }
        input[type="file"] { display: none; }
        .btn { background: #38bdf8; color: #0f172a; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; font-weight: 600; cursor: pointer; margin-top: 1rem; width: 100%; }
        .btn:hover { background: #7dd3fc; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .result { margin-top: 1.5rem; padding: 1rem; background: #0f172a; border-radius: 6px; display: none; word-break: break-all; }
        .result.show { display: block; }
        .url-input { width: 100%; padding: 0.75rem; background: #0f172a; border: 1px solid #334155; border-radius: 6px; color: #e2e8f0; font-family: monospace; font-size: 0.85rem; }
        .copy-btn { margin-top: 0.5rem; background: #475569; color: #e2e8f0; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; width: 100%; }
        .copy-btn:hover { background: #64748b; }
        .warning { color: #fca5a5; font-size: 0.8rem; margin-top: 1rem; }
        .mc-hint { color: #86efac; font-size: 0.85rem; margin-top: 0.5rem; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🎮 JustMC File Host</h1>
        <p>Загрузи JSON модуль → получи прямую ссылку → файл удалится через 20 мин</p>

        <div class="drop-zone" id="dropZone">
            <p>Перетащи файл сюда<br>или нажми для выбора</p>
            <input type="file" id="fileInput" accept=".json">
        </div>

        <button class="btn" id="uploadBtn" disabled>Загрузить</button>

        <div class="result" id="result">
            <div style="margin-bottom:0.5rem; font-size:0.85rem; color:#94a3b8;">Прямая ссылка для JustMC:</div>
            <input type="text" class="url-input" id="urlInput" readonly>
            <button class="copy-btn" id="copyBtn">Скопировать ссылку</button>
            <div class="mc-hint">Команда в игре:<br>/module loadUrl <span id="mcCommand"></span></div>
        </div>

        <div class="warning">⚠️ Файл автоматически удалится через 20 минут после загрузки</div>
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');
        const result = document.getElementById('result');
        const urlInput = document.getElementById('urlInput');
        const copyBtn = document.getElementById('copyBtn');
        const mcCommand = document.getElementById('mcCommand');

        let selectedFile = null;

        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                handleFile(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                handleFile(e.target.files[0]);
            }
        });

        function handleFile(file) {
            if (!file.name.endsWith('.json')) {
                alert('Загружай только .json файлы!');
                return;
            }
            selectedFile = file;
            dropZone.innerHTML = '<p style="color:#38bdf8">✓ Выбран: ' + file.name + '</p><br>Размер: ' + (file.size/1024).toFixed(1) + ' KB';
            uploadBtn.disabled = false;
            result.classList.remove('show');
        }

        uploadBtn.addEventListener('click', async () => {
            if (!selectedFile) return;
            const formData = new FormData();
            formData.append('file', selectedFile);

            uploadBtn.textContent = 'Загрузка...';
            uploadBtn.disabled = true;

            try {
                const res = await fetch('/upload', { method: 'POST', body: formData });
                const data = await res.json();

                if (data.url) {
                    const fullUrl = window.location.origin + data.url;
                    urlInput.value = fullUrl;
                    mcCommand.textContent = fullUrl;
                    result.classList.add('show');
                    uploadBtn.textContent = 'Загрузить ещё';
                    uploadBtn.disabled = false;
                    selectedFile = null;
                    dropZone.innerHTML = '<p>Перетащи файл сюда<br>или нажми для выбора</p>';
                } else {
                    alert('Ошибка: ' + (data.error || 'неизвестно'));
                    uploadBtn.textContent = 'Загрузить';
                    uploadBtn.disabled = false;
                }
            } catch (err) {
                alert('Ошибка сети: ' + err.message);
                uploadBtn.textContent = 'Загрузить';
                uploadBtn.disabled = false;
            }
        });

        copyBtn.addEventListener('click', () => {
            urlInput.select();
            document.execCommand('copy');
            copyBtn.textContent = 'Скопировано!';
            setTimeout(() => copyBtn.textContent = 'Скопировать ссылку', 1500);
        });
    </script>
</body>
</html>"""


@app.route("/")
def index():
    return HTML_PAGE, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Generate unique filename to avoid collisions
    ext = os.path.splitext(file.filename)[1] or ".json"
    unique_name = f"{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(FILES_DIR, unique_name)
    file.save(filepath)

    # Track upload time for cleanup
    file_times[unique_name] = datetime.now()

    return jsonify({
        "url": f"/files/{unique_name}",
        "filename": unique_name,
        "expires_in_minutes": DELETE_AFTER_MINUTES
    }), 200


@app.route("/files/<path:filename>")
def serve_file(filename):
    filepath = os.path.join(FILES_DIR, filename)
    if not os.path.exists(filepath):
        abort(404)

    # Detect mimetype
    mimetype = "application/json" if filename.endswith(".json") else "application/octet-stream"
    response = send_from_directory(FILES_DIR, filename, mimetype=mimetype)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET"
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.route("/health")
def health():
    return jsonify({"status": "ok", "files_count": len(os.listdir(FILES_DIR))})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
