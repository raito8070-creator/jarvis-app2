from flask import Flask, render_template, request, jsonify
import os
from google import genai

app = Flask(__name__)

# ========================================
# Gemini API 設定
# ========================================

API_KEY = os.environ.get("GEMINI_API_KEY")

client = None

if API_KEY:
    try:
        client = genai.Client(api_key=API_KEY)
        print("Gemini client: ONLINE")
    except Exception as e:
        print("Gemini client error:", repr(e))
        client = None
else:
    print("GEMINI_API_KEY: NOT SET")


# ========================================
# J.A.R.V.I.S. 設定
# ========================================

SYSTEM_PROMPT = """
あなたはJ.A.R.V.I.S.というAIアシスタントです。

ユーザーのことを「サー」と呼んでください。

【話し方】
- 日本語で自然に回答する
- 丁寧で冷静に話す
- 優秀なAI執事のように話す
- 必要に応じて「かしこまりました、サー。」を使う
- 無駄に長くしない
- 質問には具体的に答える
- 分からないことは正直に伝える

あなたはユーザーをサポートするAIアシスタントです。
"""


# ========================================
# トップページ
# ========================================

@app.route("/")
def home():
    return render_template("index.html")


# ========================================
# AIチャット
# ========================================

@app.route("/chat", methods=["POST"])
def chat():

    try:

        # ------------------------------
        # データ取得
        # ------------------------------

        data = request.get_json(silent=True) or {}

        message = str(
            data.get("message", "")
        ).strip()

        history = data.get("history", [])


        # ------------------------------
        # メッセージ確認
        # ------------------------------

        if not message:

            return jsonify({
                "reply": "ご用件を入力してください、サー。",
                "error": False
            })


        # ------------------------------
        # APIキー確認
        # ------------------------------

        if not API_KEY:

            print("ERROR: GEMINI_API_KEY is not set")

            return jsonify({
                "reply": (
                    "申し訳ありません、サー。\n"
                    "Gemini APIキーが設定されていません。"
                ),
                "error": True
            })


        # ------------------------------
        # Gemini Client確認
        # ------------------------------

        if client is None:

            print("ERROR: Gemini client is None")

            return jsonify({
                "reply": (
                    "申し訳ありません、サー。\n"
                    "Geminiクライアントを起動できませんでした。"
                ),
                "error": True
            })


        # ========================================
        # 会話を作成
        # ========================================

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
                        "\nユーザー："
                        + text
                    )


                elif role == "assistant":

                    conversation += (
                        "\nJ.A.R.V.I.S.："
                        + text
                    )


        conversation += (
            "\n\n【今回のユーザーの発言】\n"
        )

        conversation += message


        # ========================================
        # Geminiへ送信
        # ========================================

        print("================================")
        print("Gemini request:")
        print(message)
        print("================================")


        response = client.models.generate_content(

            model="gemini-2.5-flash",

            contents=conversation

        )


        # ========================================
        # AI回答取得
        # ========================================

        reply = getattr(
            response,
            "text",
            None
        )


        if not reply:

            print("ERROR: Gemini returned no text")

            return jsonify({
                "reply": (
                    "申し訳ありません、サー。\n"
                    "Geminiから回答を取得できませんでした。"
                ),
                "error": True
            })


        reply = reply.strip()


        print("================================")
        print("Gemini response:")
        print(reply)
        print("================================")


        # ========================================
        # 返答
        # ========================================

        return jsonify({

            "reply": reply,

            "error": False

        })


    # ========================================
    # エラー処理
    # ========================================

    except Exception as e:

        error_message = repr(e)

        print("================================")
        print("J.A.R.V.I.S. ERROR:")
        print(error_message)
        print("================================")


        return jsonify({

            "reply": (
                "申し訳ありません、サー。\n"
                "Geminiとの通信に失敗しました。\n\n"
                "ERROR: "
                + error_message
            ),

            "error": True

        }), 500


# ========================================
# ヘルスチェック
# ========================================

@app.route("/health")
def health():

    return jsonify({

        "status": "online",

        "assistant": "J.A.R.V.I.S.",

        "api": bool(API_KEY)

    })


# ========================================
# 起動
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
