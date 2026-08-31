from flask import Flask, render_template, request, jsonify
import os
from google import genai

app = Flask(__name__)

# ==========================================
# Gemini API 設定
# ==========================================

API_KEY = os.environ.get("GEMINI_API_KEY")

client = None

if API_KEY:
    try:
        client = genai.Client(api_key=API_KEY)
    except Exception as e:
        print("Gemini Client Error:", repr(e))
        client = None


# ==========================================
# J.A.R.V.I.S. SYSTEM PROMPT
# ==========================================

SYSTEM_PROMPT = """
あなたはJ.A.R.V.I.S.というAIアシスタントです。

ユーザーのことを「サー」と呼んでください。

【人格】
・冷静
・丁寧
・非常に優秀
・落ち着いたAI執事
・親切
・自然な日本語

【話し方】
・基本的に日本語
・無駄に長くしない
・質問には具体的に回答する
・必要に応じて「かしこまりました、サー。」を使用する
・難しい内容は分かりやすく説明する
・分からないことは推測せず、正直に伝える

【重要】
ユーザーとの会話を自然につなげてください。

あなたはユーザー専用のAIアシスタント
J.A.R.V.I.S.です。
"""


# ==========================================
# トップページ
# ==========================================

@app.route("/")
def index():
    return render_template("index.html")


# ==========================================
# ヘルスチェック
# ==========================================

@app.route("/health")
def health():

    return jsonify({
        "status": "online",
        "assistant": "J.A.R.V.I.S.",
        "api": bool(API_KEY),
        "model": "gemini-3.6-flash"
    })


# ==========================================
# AIチャット
# ==========================================

@app.route("/chat", methods=["POST"])
def chat():

    try:

        # --------------------------------------
        # JSON取得
        # --------------------------------------

        data = request.get_json(silent=True) or {}

        message = str(
            data.get("message", "")
        ).strip()

        history = data.get("history", [])


        # --------------------------------------
        # 空メッセージ
        # --------------------------------------

        if not message:

            return jsonify({
                "reply": "ご用件を入力してください、サー。",
                "error": False
            })


        # --------------------------------------
        # APIキー確認
        # --------------------------------------

        if not API_KEY:

            return jsonify({
                "reply": (
                    "申し訳ありません、サー。"
                    "Gemini APIキーが設定されていません。"
                ),
                "error": True
            })


        # --------------------------------------
        # Gemini Client確認
        # --------------------------------------

        if client is None:

            return jsonify({
                "reply": (
                    "申し訳ありません、サー。"
                    "Geminiクライアントを初期化できませんでした。"
                ),
                "error": True
            })


        # --------------------------------------
        # 会話履歴作成
        # --------------------------------------

        conversation = SYSTEM_PROMPT

        conversation += "\n\n【これまでの会話】\n"


        # 最大20件まで
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


        # --------------------------------------
        # 現在のメッセージ
        # --------------------------------------

        conversation += (
            "\n\n【今回のユーザーの発言】\n"
        )

        conversation += message


        # --------------------------------------
        # Gemini API
        # --------------------------------------

        response = client.models.generate_content(

            model="gemini-3.6-flash",

            contents=conversation

        )


        # --------------------------------------
        # 返答取得
        # --------------------------------------

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


        # --------------------------------------
        # 正常終了
        # --------------------------------------

        return jsonify({

            "reply": reply.strip(),

            "error": False

        })


    # ==========================================
    # エラー処理
    # ==========================================

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


        return jsonify({

            "reply": (
                "申し訳ありません、サー。"
                "Geminiとの通信中にエラーが発生しました。"
            ),

            "error": True

        })


# ==========================================
# Render用起動
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
