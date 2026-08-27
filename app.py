import os
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

SYSTEM_PROMPT = """
あなたは映画『アイアンマン』に登場する、トニー・スタークのAIアシスタント「J.A.R.V.I.S.（ジャービス）」です。
以下のルールを厳格に守って回答してください。

1. 立場: あなたはユーザーに絶対の忠誠を誓う、洗練された優秀なAI執事です。
2. 口調: 丁寧で冷静、プロフェッショナルなトーンを維持してください。
3. 一人称/二人称: 一人称は「私」または使用せず、ユーザーを「サー (Sir)」または「ボス」と呼んでください。
4. 応答スタイル: 簡潔で無駄のない効率的な言葉遣いを心がけ、「かしこまりました、サー。」等の確認フレーズを入れてから回答してください。
"""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_msg = request.json.get("message", "")
        if not user_msg:
            return jsonify({"reply": "メッセージが空です、サー。"}), 400

        chat_session = model.start_chat(history=[])
        full_prompt = f"{SYSTEM_PROMPT}\n\nユーザーの入力: {user_msg}\n\nJ.A.R.V.I.S.の回答:"
        response = chat_session.send_message(full_prompt)
        
        reply_text = response.text if response.text else "申し訳ありません、サー。データ接続に問題が発生しました。"
        return jsonify({"reply": reply_text})
    except Exception as e:
        return jsonify({"reply": f"申し訳ありません、サー。エラーが発生しました: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
