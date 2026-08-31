import os
from flask import Flask, request, jsonify, send_from_directory
from google import genai

app = Flask(__name__, static_folder="static")

# =========================================================
# 設定
# =========================================================

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# Renderの環境変数で変更可能
MODEL_NAME = os.environ.get(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)

# =========================================================
# Geminiクライアント
# =========================================================

client = None

if API_KEY:
    try:
        client = genai.Client(api_key=API_KEY)
        print("Gemini client initialized.")
    except Exception as e:
        print("Gemini client initialization error:", e)
else:
    print("WARNING: GEMINI_API_KEY is not set.")


# =========================================================
# J.A.R.V.I.S. システムプロンプト
# =========================================================

SYSTEM_PROMPT = """
あなたはJ.A.R.V.I.S.という名前のAIアシスタントです。

話し方:
- 丁寧な日本語
- 少し未来的で落ち着いた執事のような口調
- ユーザーを「サー」と呼ぶことがある
- 必要以上に堅苦しくしない
- 質問には分かりやすく答える
- 分からないことを勝手に作らない
- 日本語で質問されたら基本的に日本語で答える

例:
「承知しました、サー。」
「はい、サー。確認いたします。」
「申し訳ありません、サー。現在その情報を確認できません。」

ただし、毎回必ず「サー」を付ける必要はありません。
自然な会話を優先してください。
"""


# =========================================================
# ホームページ
# =========================================================

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# =========================================================
# ヘルスチェック
# =========================================================

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "gemini_key_configured": bool(API_KEY),
        "model": MODEL_NAME
    })


# =========================================================
# Gemini APIテスト
# =========================================================

@app.route("/test-gemini")
def test_gemini():

    if not API_KEY:
        return jsonify({
            "success": False,
            "error": "GEMINI_API_KEY がRenderに設定されていません。"
        }), 500

    if client is None:
        return jsonify({
            "success": False,
            "error": "Geminiクライアントの初期化に失敗しました。"
        }), 500

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents="「接続テスト成功」とだけ日本語で答えてください。"
        )

        return jsonify({
            "success": True,
            "response": response.text
        })

    except Exception as e:

        error_text = str(e)

        print("Gemini TEST ERROR:")
        print(error_text)

        return jsonify({
            "success": False,
            "error": error_text
        }), 500


# =========================================================
# チャット
# =========================================================

@app.route("/chat", methods=["POST"])
def chat():

    if not API_KEY:
        return jsonify({
            "success": False,
            "error": "GEMINI_API_KEY が設定されていません。"
        }), 500

    if client is None:
        return jsonify({
            "success": False,
            "error": "Geminiクライアントを初期化できませんでした。"
        }), 500

    try:

        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "error": "リクエストデータがありません。"
            }), 400

        user_message = data.get("message", "")

        if not isinstance(user_message, str):
            return jsonify({
                "success": False,
                "error": "messageは文字列で指定してください。"
            }), 400

        user_message = user_message.strip()

        if not user_message:
            return jsonify({
                "success": False,
                "error": "メッセージを入力してください。"
            }), 400

        # 会話履歴
        history = data.get("history", [])

        # 長すぎる履歴を防止
        if not isinstance(history, list):
            history = []

        history = history[-10:]

        # =====================================================
        # Geminiへ送る内容
        # =====================================================

        conversation = SYSTEM_PROMPT + "\n\n"

        for item in history:

            if not isinstance(item, dict):
                continue

            role = item.get("role", "")
            text = item.get("content", "")

            if not text:
                continue

            if role == "user":
                conversation += f"ユーザー: {text}\n"

            elif role in ["assistant", "model"]:
                conversation += f"J.A.R.V.I.S.: {text}\n"

        conversation += f"\nユーザー: {user_message}\n"
        conversation += "J.A.R.V.I.S.:"

        # =====================================================
        # Gemini API
        # =====================================================

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=conversation
        )

        answer = response.text

        if not answer:
            answer = "申し訳ありません、サー。応答を取得できませんでした。"

        return jsonify({
            "success": True,
            "response": answer,
            "model": MODEL_NAME
        })

    except Exception as e:

        error_text = str(e)

        print("=" * 60)
        print("J.A.R.V.I.S. GEMINI ERROR")
        print(error_text)
        print("=" * 60)

        # APIキー関連
        lower_error = error_text.lower()

        if (
            "api key" in lower_error
            or "api_key" in lower_error
            or "401" in lower_error
            or "unauthenticated" in lower_error
            or "permission denied" in lower_error
        ):

            message = (
                "申し訳ありません、サー。"
                "Gemini APIキーを確認してください。"
                "RenderのGEMINI_API_KEYが正しく設定されているか確認してください。"
            )

        # モデル関連
        elif (
            "model" in lower_error
            and (
                "not found" in lower_error
                or "not supported" in lower_error
                or "invalid" in lower_error
            )
        ):

            message = (
                "申し訳ありません、サー。"
                f"指定されたGeminiモデル「{MODEL_NAME}」を利用できません。"
                "GEMINI_MODELの設定を確認してください。"
            )

        # 混雑
        elif "503" in lower_error or "unavailable" in lower_error:

            message = (
                "申し訳ありません、サー。"
                "現在Geminiサーバーが混雑しています。"
                "少し時間を置いて再度お試しください。"
            )

        else:

            message = (
                "申し訳ありません、サー。"
                "Geminiとの通信中にエラーが発生しました。"
            )

        return jsonify({
            "success": False,
            "error": message,
            "details": error_text
        }), 500


# =========================================================
# 404
# =========================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "ページが見つかりません。"
    }), 404


# =========================================================
# サーバー起動
# =========================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    print("=" * 60)
    print("J.A.R.V.I.S. SERVER")
    print("=" * 60)
    print("PORT:", port)
    print("MODEL:", MODEL_NAME)
    print("API KEY:", "SET" if API_KEY else "NOT SET")
    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
