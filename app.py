from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True) or {}

    message = str(
        data.get("message", "")
    ).strip()

    if not message:
        return jsonify({
            "reply": "ご用件を入力してください、サー。"
        })


    # --------------------------------
    # Gemini API
    # --------------------------------

    api_key = os.environ.get(
        "GEMINI_API_KEY"
    )

    if not api_key:

        return jsonify({
            "reply":
            "申し訳ありません、サー。"
            "GEMINI_API_KEYが設定されていません。"
        })


    try:

        from google import genai

        client = genai.Client(
            api_key=api_key
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=(
                "あなたはJ.A.R.V.I.S.という名前の"
                "日本語AIアシスタントです。"
                "丁寧で少し執事のような口調で回答してください。"
                "ユーザーからの質問に分かりやすく答えてください。\n\n"
                "ユーザー: "
                + message
            )
        )

        reply = response.text

        return jsonify({
            "reply": reply
        })


    except Exception as e:

        print("Gemini error:", e)

        return jsonify({
            "reply":
            "申し訳ありません、サー。"
            "AIとの通信中にエラーが発生しました。"
        })


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
