from flask import Flask, render_template, request, jsonify
import os
import time
from google import genai

app = Flask(__name__)

# ==========================================
# Gemini設定
# ==========================================

API_KEY = os.environ.get("GEMINI_API_KEY")

if API_KEY:
    client = genai.Client(api_key=API_KEY)
else:
    client = None


# ==========================================
# J.A.R.V.I.S.設定
# ==========================================

SYSTEM_PROMPT = """
あなたはJ.A.R.V.I.S.というAIアシスタントです。

ユーザーのことを「サー」と呼んでください。

【話し方】
- 丁寧
- 冷静
- 優秀なAI執事のように話す
- 日本語で自然に回答する
- 無駄に長くしない
- 必要な場合のみ「かしこまりました、サー。」を使う
- 質問には具体的に答える
- 分からないことは正直に伝える

【重要】
あなたはユーザーをサポートするAIアシスタントです。
回答は分かりやすく、実用的にしてください。
"""


# ==========================================
# トップページ
# ==========================================

@app.route("/")
def index():
    return render_template("index.html")


# ==========================================
# Geminiに問い合わせ
# ==========================================

def ask_gemini(conversation):

    if client is None:
        raise RuntimeError("GEMINI_API_KEYが設定されていません。")

    # 最大3回まで試行
    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model="gemini-3.7-flash",
                contents=conversation
            )

            reply = getattr(response, "text", None)

            if reply:
                return reply.strip()

            raise RuntimeError("Geminiから空の回答が返されました。")

        except Exception as e:

            error_text = str(e)

            print(
                f"Gemini attempt {attempt + 1}/3:",
                repr(e)
            )

            # 503 / UNAVAILABLE / 高負荷の場合
            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "high demand" in error_text
            ):

                if attempt < 2:

                    # 2秒 → 4秒
                    wait_time = 2 ** (attempt + 1)

                    print(
                        f"Geminiが混雑しています。"
                        f"{wait_time}秒後に再試行します。"
                    )

                    time.sleep(wait_time)

                    continue

            # 503以外はそのままエラー
            raise


# ==========================================
# AIチャット
# ==========================================

@app.route("/chat", methods=["POST"])
def chat():

    try:

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

        if not API_KEY or client is None:

            return jsonify({

                "reply": (
                    "申し訳ありません、サー。"
                    "Gemini APIキーが設定されていません。"
                ),

                "error": True

            })


        # --------------------------------------
        # 会話履歴
        # --------------------------------------

        conversation = SYSTEM_PROMPT

        conversation += """

【これまでの会話】
"""


        # 最大20件
        for item in history[-20:]:

            if not isinstance(item, dict):
                continue

            role = item.get("role", "")
            text = str(item.get("text", "")).strip()

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
        # 今回の発言
        # --------------------------------------

        conversation += """

【今回のユーザーの発言】
"""

        conversation += message


        # --------------------------------------
        # Geminiへ送信
        # --------------------------------------

        reply = ask_gemini(conversation)


        # --------------------------------------
        # 返答
        # --------------------------------------

        return jsonify({

            "reply": reply,

            "error": False

        })


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


        error_text = str(e)


        # --------------------------------------
        # Gemini混雑
        # --------------------------------------

        if (
            "503" in error_text
            or "UNAVAILABLE" in error_text
            or "high demand" in error_text
        ):

            return jsonify({

                "reply": (
                    "申し訳ありません、サー。"
                    "現在Geminiのサーバーが混雑しています。"
                    "少し時間を置いて、もう一度お試しください。"
                ),

                "error": True,

                "type": "gemini_busy"

            })


        # --------------------------------------
        # その他のエラー
        # --------------------------------------

        return jsonify({

            "reply": (
                "申し訳ありません、サー。"
                "AIとの通信中にエラーが発生しました。"
            ),

            "error": True,

            "type": "server_error"

        })


# ==========================================
# 状態確認
# ==========================================

@app.route("/health")
def health():

    return jsonify({

        "status": "online",

        "assistant": "J.A.R.V.I.S.",

        "api": bool(API_KEY),

        "model": "gemini-3.7-flash"

    })


# ==========================================
# 起動
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
