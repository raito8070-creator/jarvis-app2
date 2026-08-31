from flask import Flask, render_template, request, jsonify
import os
from google import genai

app = Flask(__name__)

# =====================================
# Gemini
# =====================================

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("WARNING: GEMINI_API_KEY is not set")
    client = None
else:
    try:
        client = genai.Client(api_key=API_KEY)
        print("Gemini client initialized")
    except Exception as e:
        print("Gemini client error:", repr(e))
        client = None


MODEL = "gemini-3.7-flash"


# =====================================
# J.A.R.V.I.S.
# =====================================

SYSTEM_PROMPT = """
あなたはJ.A.R.V.I.S.というAIアシスタントです。

ユーザーのことを「サー」と呼んでください。

性格：
・冷静
・丁寧
・優秀
・親切
・AI執事のような話し方

ルール：
・日本語で自然に回答する
・回答は分かりやすくする
・必要以上に長くしない
・質問には具体的に答える
・必要に応じて「かしこまりました、サー。」を使う
・分からないことは正直に伝える

あなたはユーザー専用AI、
J.A.R.V.I.S.です。
"""


# =====================================
# トップページ
# =====================================

@app.route("/")
def index():
    return render_template("index.html")


# =====================================
# Health Check
# =====================================

@app.route("/health")
def health():

    return jsonify({
        "status": "online",
        "assistant": "J.A.R.V.I.S.",
        "api": bool(API_KEY),
        "model": MODEL
    })


# =====================================
# Chat
# =====================================

@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json(silent=True) or {}

        message = str(
            data.get("message", "")
        ).strip()

        history = data.get("history", [])


        # 空メッセージ
        if not message:

            return jsonify({
                "reply": "ご用件を入力してください、サー。",
                "error": False
            })


        # APIキーなし
        if not API_KEY:

            return jsonify({
                "reply": (
                    "申し訳ありません、サー。"
                    "Gemini APIキーが設定されていません。"
                ),
                "error": True
            })


        # Clientなし
        if client is None:

            return jsonify({
                "reply": (
                    "申し訳ありません、サー。"
                    "Geminiクライアントを初期化できませんでした。"
                ),
                "error": True
            })


        # =================================
        # 会話を作成
        # =================================

        conversation = SYSTEM_PROMPT

        conversation += "\n\n【会話履歴】\n"


        if isinstance(history, list):

            for item in history[-20:]:

                if not isinstance(item, dict):
                    continue

                role = item.get("role", "")
                text = str(
                    item.get("text", "")
                ).strip()

                if not text:
                    continue

                if role == "user":

                    conversation += (
                        f"\nユーザー：{text}"
                    )

                elif role == "assistant":

                    conversation += (
                        f"\nJ.A.R.V.I.S.：{text}"
                    )


        conversation += (
            "\n\n【今回の発言】\n"
        )

        conversation += message


        # =================================
        # Gemini
        # =================================

        print("Sending request to Gemini...")

        response = client.models.generate_content(
            model=MODEL,
            contents=conversation
        )

        print("Gemini response received")


        # =================================
        # 回答
        # =================================

        reply = getattr(
            response,
            "text",
            None
        )


        if not reply:

            reply = (
                "申し訳ありません、サー。"
                "回答を取得できませんでした。"
            )


        return jsonify({
            "reply": reply.strip(),
            "error": False
        })


    except Exception as e:

        # Renderのログに本当のエラーを出す
        print("================================")
        print("J.A.R.V.I.S. ERROR")
        print(repr(e))
        print("================================")


        return jsonify({

            "reply": (
                "申し訳ありません、サー。"
                "Geminiとの通信中にエラーが発生しました。"
            ),

            "error": True

        })


# =====================================
# Render
# =====================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
