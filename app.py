import os
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Gemini APIキー
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

genai.configure(api_key=API_KEY)

# 使用するGeminiモデル
model = genai.GenerativeModel("gemini-2.5-flash")

# J.A.R.V.I.S.の設定
SYSTEM_PROMPT = """
あなたはJ.A.R.V.I.S.というAIアシスタントです。

あなたの役割：
・ユーザーをサポートする高性能AIアシスタント
・丁寧で冷静、スマートな話し方をする
・ユーザーのことを「サー」または「ボス」と呼ぶ
・質問には分かりやすく、必要十分な回答をする
・できるだけ簡潔かつ自然に回答する

応答するときは、
「かしこまりました、サー。」
「承知しました、ボス。」
などの確認フレーズを適宜使用してください。

日本語で質問された場合は日本語で回答してください。
"""

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "reply": "申し訳ありません、サー。データを受信できませんでした。"
            }), 400

        user_msg = data.get("message", "").strip()

        if not user_msg:
            return jsonify({
                "reply": "メッセージが空です、サー。"
            }), 400

        # Geminiへ送信
        full_prompt = f"""
{SYSTEM_PROMPT}

ユーザーの入力：
{user_msg}

J.A.R.V.I.S.として回答してください。
"""

        response = model.generate_content(full_prompt)

        if response and response.text:
            reply_text = response.text
        else:
            reply_text = "申し訳ありません、サー。回答を生成できませんでした。"

        return jsonify({
            "reply": reply_text
        })

    except Exception as e:
        print("ERROR:", str(e))

        return jsonify({
            "reply": f"申し訳ありません、サー。エラーが発生しました。\n{str(e)}"
        }), 500


if __name__ == "__main__":
    # RenderのPORTを使用
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
