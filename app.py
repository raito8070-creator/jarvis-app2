import os
import base64
import requests
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

SYSTEM_PROMPT = """
あなたはJ.A.R.V.I.S.という名前の個人用AIアシスタントです。
落ち着いた未来的な執事のような日本語で話してください。
必要なときだけユーザーを「サー」と呼んでください。
回答は正確で分かりやすく、必要以上に長くしないでください。
最新情報が必要な質問では検索ツールを利用してください。
画像やPDFが渡された場合は、その内容を読み取って質問に答えてください。
危険・違法・年齢制限のあることについては安全を優先してください。
"""

def gemini_url():
    return (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{GEMINI_MODEL}:generateContent"
    )

def call_gemini(contents, use_search=False):
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
    }
    if use_search:
        payload["tools"] = [{"google_search": {}}]

    r = requests.post(
        gemini_url(),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY,
        },
        json=payload,
        timeout=90,
    )
    try:
        data = r.json()
    except ValueError:
        data = {"raw": r.text}

    if r.status_code != 200:
        print("Gemini:", r.status_code, data)
        return None, {
            "success": False,
            "error": "Gemini APIでエラーが発生しました。",
            "status": r.status_code,
            "details": data,
        }

    candidates = data.get("candidates", [])
    if not candidates:
        return None, {"success": False, "error": "Geminiから回答が返りませんでした。"}

    parts = candidates[0].get("content", {}).get("parts", [])
    reply = "".join(p.get("text", "") for p in parts if isinstance(p, dict)).strip()
    if not reply:
        return None, {"success": False, "error": "Geminiの回答本文が空でした。"}

    return reply, None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({
        "success": True,
        "status": "online",
        "model": GEMINI_MODEL,
        "api_key_set": bool(GEMINI_API_KEY),
    })

@app.route("/chat", methods=["POST"])
def chat():
    if not GEMINI_API_KEY:
        return jsonify({"success": False, "error": "RenderにGEMINI_API_KEYが設定されていません。"}), 500

    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    use_search = bool(data.get("use_search", False))
    history = data.get("history", [])

    if not message:
        return jsonify({"success": False, "error": "メッセージが空です。"}), 400

    contents = []
    if isinstance(history, list):
        for item in history[-12:]:
            role = "model" if item.get("role") == "assistant" else "user"
            text = str(item.get("text", "")).strip()
            if text:
                contents.append({"role": role, "parts": [{"text": text}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    reply, err = call_gemini(contents, use_search=use_search)
    if err:
        return jsonify(err), 502
    return jsonify({"success": True, "reply": reply})

@app.route("/analyze", methods=["POST"])
def analyze():
    if not GEMINI_API_KEY:
        return jsonify({"success": False, "error": "GEMINI_API_KEYが設定されていません。"}), 500

    image = request.files.get("image")
    prompt = request.form.get("prompt", "この画像を詳しく説明してください。").strip()
    if not image:
        return jsonify({"success": False, "error": "画像がありません。"}), 400

    mime = image.mimetype or "image/jpeg"
    raw = image.read()
    if not raw:
        return jsonify({"success": False, "error": "画像が空です。"}), 400

    contents = [{
        "role": "user",
        "parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": mime, "data": base64.b64encode(raw).decode("ascii")}},
        ],
    }]
    reply, err = call_gemini(contents)
    if err:
        return jsonify(err), 502
    return jsonify({"success": True, "reply": reply})

@app.route("/document", methods=["POST"])
def document():
    if not GEMINI_API_KEY:
        return jsonify({"success": False, "error": "GEMINI_API_KEYが設定されていません。"}), 500

    doc = request.files.get("file")
    prompt = request.form.get("prompt", "このファイルの重要点を日本語で要約してください。").strip()
    if not doc:
        return jsonify({"success": False, "error": "ファイルがありません。"}), 400

    filename = secure_filename(doc.filename or "file")
    ext = os.path.splitext(filename)[1].lower()
    raw = doc.read()

    # PDF: extract text server-side.
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            from io import BytesIO
            reader = PdfReader(BytesIO(raw))
            text = "\n".join((p.extract_text() or "") for p in reader.pages)
            text = text[:60000]
        except Exception as e:
            return jsonify({"success": False, "error": "PDFの読み取りに失敗しました。", "details": str(e)}), 400
    else:
        try:
            text = raw.decode("utf-8", errors="replace")[:60000]
        except Exception:
            text = ""

    if not text.strip():
        return jsonify({"success": False, "error": "読み取れる文字が見つかりませんでした。"}), 400

    contents = [{
        "role": "user",
        "parts": [{"text": f"{prompt}\n\nファイル名: {filename}\n\n--- ファイル内容 ---\n{text}"}],
    }]
    reply, err = call_gemini(contents)
    if err:
        return jsonify(err), 502
    return jsonify({"success": True, "reply": reply, "filename": filename})

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
