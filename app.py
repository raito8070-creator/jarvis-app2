from flask import Flask, render_template, request, jsonify
import os
from google import genai

app = Flask(__name__)

# ========================================
# Gemini API
# ========================================

API_KEY = os.environ.get("GEMINI_API_KEY")

client = None

if API_KEY:
    try:
        client = genai.Client(api_key=API_KEY)
    except Exception as e:
        print("Gemini Client Error:", repr(e))
        client = None


# ========================================
# J.A.R.V.I.S. SYSTEM
# ========================================

SYSTEM_PROMPT = """
あなたはJ.A.R.V.I.S.というAIアシスタントです。

ユーザーのことを必ず「サー」と呼んでください。

【話し方】
- 日本語で自然に話す
- 丁寧で冷静
- 優秀なAI執事のように話す
- 必要なら「かしこまりました、サー。」を使う
- 回答は分かりやすくする
- 無駄に長くしない
- 分からないことは正直に伝える

あなたはユーザーをサポートするAIアシスタントです。
"""


# ========================================
# HOME
# ========================================

@app.route("/")
def home():
    return render_template("index.html")


# ========================================
# CHAT
# ========================================

@app.route("/chat", methods=["POST"])
def chat():

    try:
        # -----------------------------
        # データ取得
        # -----------------------------

        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "reply": "申し訳ありません、サー。データを受信できませんでした。",
                "error": True
            })

        message = str(
            data.get("message", "")
        ).strip()

        history = data.get("history", [])


        # -----------------------------
        # 空メッセージ
        # -----------------------------

        if not message:
            return jsonify({
                "reply": "ご用件を入力してください、サー。",
                "error": False
            })


        # -----------------------------
        # API確認
        # -----------------------------

        if not API_KEY:

            return jsonify({
                "reply": (
                    "申し訳ありません、サー。\n"
                    "Gemini APIキーが設定されていません。"
                ),
                "error": True
            })


        if client is None:

            return jsonify({
                "reply": (
                    "申し訳ありません、サー。\n"
                    "Geminiクライアントを起動できませんでした。"
                ),
                "error": True
            })


        # -----------------------------
        # 会話履歴
        # -----------------------------

        conversation = SYSTEM_PROMPT

        conversation += "\n\n【これまでの会話】\n"

        if isinstance(history, list):

            for item in history[-10:]:

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


        # -----------------------------
        # 今回のメッセージ
        # -----------------------------

        conversation += (
            "\n\n【今回のユーザーの発言】\n"
        )

        conversation += message


        # -----------------------------
        # Gemini
        # -----------------------------

        print("Gemini request:", message)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=conversation
        )


        # -----------------------------
        # 返答取得
        # -----------------------------

        reply = getattr(
            response,
            "text",
            None
        )


        if not reply:

            reply = (
                "申し訳ありません、サー。\n"
                "AIから回答を取得できませんでした。"
            )


        print("Gemini response:", reply)

        return jsonify({
            "reply": reply.strip(),
            "error": False
        })


    # ====================================
    # エラー
    # ====================================

    except Exception as e:

        print(
            "================================"
        )

        print(
            "J.A.R.V.I.S. ERROR:"
        )

        print(
            repr(e)
        )

        print(
            "================================"
        )


        # エラー内容をサーバーログにだけ表示
        # ユーザーには安全な文章を表示

        return jsonify({

            "reply": (
                "申し訳ありません、サー。\n"
                "AIとの通信中にエラーが発生しました。"
            ),

            "error": True

        })


# ========================================
# HEALTH CHECK
# ========================================

@app.route("/health")
def health():

    return jsonify({

        "status": "online",

        "assistant": "J.A.R.V.I.S.",

        "api": bool(API_KEY)

    })


# ========================================
# START
# ========================================

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
