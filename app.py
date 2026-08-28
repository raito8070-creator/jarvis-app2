from flask import Flask, render_template, request, jsonify
import os

from google import genai

app = Flask(__name__)

# ==========================================
# J.A.R.V.I.S. CONFIG
# ==========================================

MODEL_NAME = "gemini-3.6-flash"

SYSTEM_PROMPT = """
あなたは「J.A.R.V.I.S.」という日本語AIアシスタントです。

ユーザーのことを「サー」と呼びます。

話し方：
- 丁寧
- 落ち着いている
- 少し執事のような口調
- 必要なら簡潔に答える
- 日本語で回答する
- 「かしこまりました、サー。」など自然なJ.A.R.V.I.S.風の表現を使う
- 嘘の情報を作らない
- 分からないことは分からないと伝える

例：
ユーザー：こんにちは
J.A.R.V.I.S.：こんにちは、サー。システムは正常に稼働しております。本日はどのようなご用件でしょうか？
"""

# Gemini API
API_KEY = os.environ.get("GEMINI_API_KEY")

client = None

if API_KEY:
    client = genai.Client(api_key=API_KEY)


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# CHAT API
# ==========================================

@app.route("/chat", methods=["POST"])
def chat():

    try:
        data = request.get_json(silent=True) or {}

        message = str(
            data.get("message", "")
        ).strip()

        history = data.get("history", [])

        if not message:
            return jsonify({
                "reply": "ご用件を入力してください、サー。"
            })

        # APIキー確認
        if not API_KEY or client is None:
            return jsonify({
                "reply": (
                    "申し訳ありません、サー。"
                    "GEMINI_API_KEYが設定されていません。"
                ),
                "error": True
            })

        # ======================================
        # 会話履歴をテキストとして整理
        # ======================================

        conversation = SYSTEM_PROMPT + "\n\n"

        # 最大20ターン程度
        for item in history[-20:]:

            role = item.get("role", "")
            text = item.get("text", "")

            if not text:
                continue

            if role == "user":
                conversation += f"ユーザー：{text}\n"

            elif role == "assistant":
                conversation += f"J.A.R.V.I.S.：{text}\n"

        conversation += f"\nユーザー：{message}\n"
        conversation += "J.A.R.V.I.S.："

        # ======================================
        # Gemini
        # ======================================

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=conversation
        )

        reply = getattr(response, "text", None)

        if not reply:
            reply = "申し訳ありません、サー。回答を生成できませんでした。"

        return jsonify({
            "reply": reply.strip(),
            "error": False
        })

    except Exception as e:

        print("CHAT ERROR:", repr(e))

        return jsonify({
            "reply": (
                "申し訳ありません、サー。"
                "AIとの通信中にエラーが発生しました。"
            ),
            "error": True
        }), 200


# ==========================================
# HEALTH CHECK
# ==========================================

@app.route("/health")
def health():

    return jsonify({
        "status": "online",
        "assistant": "J.A.R.V.I.S.",
        "model": MODEL_NAME,
        "api": bool(API_KEY)
    })


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
