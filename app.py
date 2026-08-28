import os
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

client = genai.Client(api_key=API_KEY)

SYSTEM_PROMPT = """
あなたはJ.A.R.V.I.S.という高性能AIアシスタントです。

ユーザーを「サー」または「ボス」と呼んでください。
丁寧で冷静、スマートな口調で話してください。

回答は日本語で、分かりやすく簡潔にしてください。

必要に応じて、
「かしこまりました、サー。」
「承知しました、ボス。」
などの確認フレーズを使用してください。
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

        prompt = f"""
{SYSTEM_PROMPT}

ユーザー：
{user_msg}

J.A.R.V.I.S.として回答してください。
"""

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        reply = response.text

        if not reply:
            reply = "申し訳ありません、サー。回答を生成できませんでした。"

        return jsonify({"reply": reply})

    except Exception as e:
        print("ERROR:", str(e))

        return jsonify({
            "reply": f"申し訳ありません、サー。エラーが発生しました。\n{str(e)}"
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
