from flask import Flask, render_template, request, jsonify
import os
from google import genai

app = Flask(__name__)

# ==========================================
# Gemini API
# ==========================================

API_KEY = os.environ.get("GEMINI_API_KEY")

client = None

if API_KEY:
    try:
        client = genai.Client(api_key=API_KEY)
    except Exception as e:
        print("Gemini client error:", repr(e))


# ==========================================
# J.A.R.V.I.S. 設定
# ==========================================

SYSTEM_PROMPT = """
あなたはJ.A.R.V.I.S.というAIアシスタントです。

ユーザーのことを「サー」と呼んでください。

話し方：
- 丁寧
- 冷静
- 優秀なAI執事のように話す
- 自然な日本語
- 回答は分かりやすく簡潔にする
- 必要に応じて「かしこまりました、サー。」を使う
- 質問には具体的に答える
- 分からないことは正直に伝える

あなたはユーザーをサポートするAIアシスタントです。
"""


# ==========================================
# トップページ
# ==========================================

@app.route("/")
def index():
    return render_template("index.html")


# ==========================================
# AIチャット
# ==========================================

@app.route("/chat", methods=["POST"])
def chat():

    try:
        data = request.get_json(silent=True) or {}

        message = str(
            data.get("message", "")
        ).strip()

        history = data.get("history", [])

        # ----------------------------------
        # 空メッセージ
        # ----------------------------------

        if not message:
            return jsonify({
                "reply": "ご用件を入力してください、サー。",
                "error": False
            })


        # ----------------------------------
        # APIキー確認
        # ----------------------------------

        if not API_KEY or client is None:

            return jsonify({
                "reply": (
                    "申し訳ありません、サー。"
                    "Gemini APIキーが設定されていません。"
                ),
                "error": True
            })


        # ----------------------------------
        # 会話履歴
        # ----------------------------------

        conversation = SYSTEM_PROMPT

        conversation += "\n\nこれまでの会話:\n"

        for item in history[-20:]:

            if not isinstance(item, dict):
                continue

            role = item.get("role", "")
            text = str(item.get("text", "")).strip()

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
            "\n\n今回のユーザーの発言：\n"
        )

        conversation += message


        # ==================================
        # Geminiへ送信
        # ==================================

        response = client.models.generate_content(

            # 現在使用するモデル
            model="gemini-3.7-flash",

            contents=conversation

        )


        # ==================================
        # 返答取得
        # ==================================

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

        # Renderのログには詳細を残す
        print(
            "J.A.R.V.I.S. ERROR:",
            repr(e)
        )

        # ユーザー画面には詳細なエラーを表示しない
        return jsonify({

            "reply": (
                "申し訳ありません、サー。"
                "Geminiとの通信に失敗しました。"
                "しばらくしてからもう一度お試しください。"
            ),

            "error": True

        })


# ==========================================
# ヘルスチェック
# ==========================================

@app.route("/health")
def health():

    return jsonify({

        "status": "online",

        "assistant": "J.A.R.V.I.S.",

        "api": bool(API_KEY)

    })


# ==========================================
# 起動
# ==========================================

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
