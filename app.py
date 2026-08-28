from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

# ==============================
# Gemini
# ==============================
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")

if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None


SYSTEM_PROMPT = """
あなたは J.A.R.V.I.S. という日本語AIアシスタントです。

話し方：
- 丁寧
- 少し執事・AIアシスタント風
- ユーザーのことを「サー」と呼ぶ
- 自然な日本語で回答する
- 回答は分かりやすく簡潔にする

最初の挨拶：
「かしこまりました、サー。システムは正常に起動しています。何をお手伝いしましょうか？」
"""


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "")).strip()

        if not message:
            return jsonify({
                "reply": "ご用件を入力してください、サー。"
            })

        # APIキー確認
        if not api_key or not client:
            return jsonify({
                "reply": "申し訳ありません、サー。GEMINI_API_KEYが設定されていません。"
            })

        # Geminiへ送信
        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=message,
            config={
                "system_instruction": SYSTEM_PROMPT
            }
        )

        reply = response.text

        if not reply:
            reply = "申し訳ありません、サー。回答を取得できませんでした。"

        return jsonify({
            "reply": reply
        })

    except Exception as e:
        print("Gemini Error:", repr(e))

        return jsonify({
            "reply": "申し訳ありません、サー。AIとの通信中にエラーが発生しました。"
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
