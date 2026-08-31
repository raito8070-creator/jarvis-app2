import os
import requests

from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# ==============================
# Gemini設定
# ==============================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 現在利用可能なGeminiモデル
MODEL = "gemini-3.7-flash"

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/"
    f"v1beta/models/{MODEL}:generateContent"
)

# ==============================
# J.A.R.V.I.S.設定
# ==============================

SYSTEM_PROMPT = """
あなたはJ.A.R.V.I.S.という名前のAIアシスタントです。

ユーザーには丁寧な日本語で対応してください。

基本的な話し方:
- 丁寧
- 冷静
- 少し未来的
- 執事のような口調
- 必要に応じて「サー」と呼ぶ
- ただし不自然に毎回「サー」を付けない

回答は分かりやすくしてください。

ユーザーから質問された場合は、
可能な限り正確に答えてください。

ユーザーが「こんにちは」と言った場合は、
自然に挨拶してください。

あなたはJ.A.R.V.I.S.です。
"""

# ==============================
# ホーム画面
# ==============================

@app.route("/")
def index():
    return render_template("index.html")


# ==============================
# ヘルスチェック
# ==============================

@app.route("/health")
def health():
    return jsonify({
        "success": True,
        "status": "online",
        "model": MODEL,
        "api_key": bool(GEMINI_API_KEY)
    })


# ==============================
# チャット
# ==============================

@app.route("/chat", methods=["POST"])
def chat():

    # APIキー確認
    if not GEMINI_API_KEY:
        return jsonify({
            "success": False,
            "error": "GEMINI_API_KEYがRenderに設定されていません。"
        }), 500

    try:
        data = request.get_json(silent=True) or {}

        user_message = data.get("message", "")

        if not user_message:
            return jsonify({
                "success": False,
                "error": "メッセージが空です。"
            }), 400

        # Geminiへ送信する内容
        prompt = SYSTEM_PROMPT + "\n\nユーザー:\n" + user_message

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048
            }
        }

        # ==============================
        # Gemini APIへ送信
        # ==============================
        response = requests.post(
            GEMINI_URL,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY
            },
            json=payload,
            timeout=60
        )

        # APIエラー
        if response.status_code != 200:

            try:
                error_data = response.json()
            except Exception:
                error_data = response.text

            print("Gemini API ERROR:")
            print(error_data)

            return jsonify({
                "success": False,
                "error": "Gemini APIでエラーが発生しました。",
                "details": error_data
            }), response.status_code

        result = response.json()

        # ==============================
        # Geminiの回答を取得
        # ==============================

        try:
            reply = result["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):

            print("予期しないGeminiレスポンス:")
            print(result)

            return jsonify({
                "success": False,
                "error": "Geminiから正常な回答を取得できませんでした。",
                "details": result
            }), 500

        return jsonify({
            "success": True,
            "reply": reply
        })

    except requests.exceptions.Timeout:

        return jsonify({
            "success": False,
            "error": "Geminiとの通信がタイムアウトしました。"
        }), 504

    except requests.exceptions.RequestException as e:

        print("通信エラー:", e)

        return jsonify({
            "success": False,
            "error": "Geminiとの通信に失敗しました。"
        }), 500

    except Exception as e:

        print("予期しないエラー:", e)

        return jsonify({
            "success": False,
            "error": "サーバー内部でエラーが発生しました。"
        }), 500


# ==============================
# Render起動
# ==============================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
