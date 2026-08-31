import os
import time

from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

# =========================
# Gemini設定
# =========================

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY が設定されていません。")

client = genai.Client(api_key=API_KEY)

MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """
あなたはJ.A.R.V.I.S.です。

ユーザーを必ず「サー」と呼んでください。

あなたは高度なAIアシスタントとして、
落ち着いた丁寧な日本語で応答してください。

基本ルール：

・ユーザーを「サー」と呼ぶ
・無駄に長くしない
・質問には直接答える
・必要なら箇条書きを使う
・親切で自然な日本語を使う
・自分をChatGPTとは名乗らない
・自分をJ.A.R.V.I.S.として振る舞う
・「申し訳ありません、現在テキストのみです」
  のような音声機能に関する説明はしない
・回答は読み上げても自然な文章にする
"""

# =========================
# Gemini問い合わせ
# =========================

def ask_gemini(message):
    last_error = None

    # 503など一時的なエラーに備えて3回試行
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=message,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.7,
                    max_output_tokens=1000
                )
            )

            if response.text:
                return response.text.strip()

            return "申し訳ありません、回答を取得できませんでした、サー。"

        except Exception as e:
            last_error = e
            error_text = str(e)

            print("Gemini ERROR:", error_text)

            # 503 / 429 の場合は少し待って再試行
            if "503" in error_text or "UNAVAILABLE" in error_text:
                time.sleep(2 * (attempt + 1))
                continue

            if "429" in error_text:
                time.sleep(3 * (attempt + 1))
                continue

            break

    return (
        "申し訳ありません、サー。"
        "現在、AIサーバーとの通信が混雑しております。"
        "少し時間を置いて、もう一度お試しください。"
    )


# =========================
# メインページ
# =========================

@app.route("/")
def index():
    return render_template("index.html")


# =========================
# チャットAPI
# =========================

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = data.get("message", "").strip()

        if not message:
            return jsonify({
                "success": False,
                "error": "メッセージが空です。"
            }), 400

        answer = ask_gemini(message)

        return jsonify({
            "success": True,
            "response": answer
        })

    except Exception as e:
        print("SERVER ERROR:", str(e))

        return jsonify({
            "success": False,
            "error": "サーバー内部でエラーが発生しました。"
        }), 500


# =========================
# ヘルスチェック
# =========================

@app.route("/health")
def health():
    return jsonify({
        "status": "online",
        "system": "J.A.R.V.I.S."
    })


# =========================
# Render起動
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
