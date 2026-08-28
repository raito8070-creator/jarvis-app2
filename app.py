from flask import Flask, render_template, request, jsonify
import os
from google import genai

app = Flask(__name__)

# ==============================
# Gemini設定
# ==============================

API_KEY = os.environ.get("GEMINI_API_KEY")

if API_KEY:
    client = genai.Client(api_key=API_KEY)
else:
    client = None


# ==============================
# J.A.R.V.I.S.設定
# ==============================

SYSTEM_PROMPT = """
あなたはJ.A.R.V.I.S.というAIアシスタントです。

ユーザーのことを「サー」と呼んでください。

話し方：
- 丁寧で冷静
- 優秀なAI執事のように話す
- 無駄に長くしない
- 日本語で自然に回答する
- 必要に応じて「かしこまりました、サー。」を使う
- 質問には具体的に答える
- 分からないことは、分からないと正直に伝える

あなたはユーザーをサポートするAIアシスタントです。
"""


# ==============================
# トップページ
# ==============================

@app.route("/")
def index():
    return render_template("index.html")


# ==============================
# AIチャット
# ==============================

@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json(silent=True) or {}

        message = str(
            data.get("message", "")
        ).strip()

        history = data.get("history", [])


        # メッセージが空の場合

        if not message:

            return jsonify({
                "reply": "ご用件を入力してください、サー。"
            })


        # APIキー確認

        if not API_KEY or client is None:

            return jsonify({
                "reply": (
                    "申し訳ありません、サー。"
                    "Gemini APIキーが設定されていません。"
                ),
                "error": True
            })


        # ==========================
        # 会話履歴を作成
        # ==========================

        conversation = SYSTEM_PROMPT

        conversation += "\n\nこれまでの会話:\n"


        for item in history[-20:]:

            role = item.get("role", "")
            text = item.get("text", "")

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


        conversation += "\n\n今回のユーザーの発言："
        conversation += message


        # ==========================
        # Geminiへ送信
        # ==========================

        response = client.models.generate_content(

            model="gemini-3.7-flash",

            contents=conversation

        )


        # ==========================
        # AIの返答
        # ==========================

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

        print(
            "J.A.R.V.I.S. ERROR:",
            repr(e)
        )

        return jsonify({

            "reply": (
                "申し訳ありません、サー。"
                "AIとの通信中にエラーが発生しました。"
            ),

            "error": True

        })


# ==============================
# 状態確認
# ==============================

@app.route("/health")
def health():

    return jsonify({

        "status": "online",

        "assistant": "J.A.R.V.I.S.",

        "api": bool(API_KEY)

    })


# ==============================
# 起動
# ==============================

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
