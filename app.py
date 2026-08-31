import os
import time

from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types


# ==========================================
# Flask
# ==========================================

app = Flask(__name__)


# ==========================================
# Gemini設定
# ==========================================

API_KEY = os.environ.get("GEMINI_API_KEY")

MODEL = "gemini-2.5-flash"

client = None

if API_KEY:
    client = genai.Client(
        api_key=API_KEY
    )


# ==========================================
# J.A.R.V.I.S.設定
# ==========================================

SYSTEM_PROMPT = """
あなたはJ.A.R.V.I.S.というAIアシスタントです。

ユーザーのことを「サー」と呼んでください。

話し方：
- 丁寧
- 冷静
- 自然な日本語
- 優秀なAI執事のように話す
- 無駄に長くしない
- 質問には具体的に答える

重要：
ユーザーが音声について質問していない限り、
音声機能について説明しないでください。

「現在テキストのみです」
「音声には対応していません」
「端末の読み上げ機能を使ってください」
などの説明を勝手にしないでください。

あなたはJ.A.R.V.I.S.として
ユーザーをサポートしてください。
"""


# ==========================================
# Gemini問い合わせ
# ==========================================

def ask_gemini(message, history=None):

    if client is None:

        print("================================")
        print("GEMINI ERROR")
        print("GEMINI_API_KEY が設定されていません")
        print("================================")

        return (
            "申し訳ありません、サー。"
            "Gemini APIキーが設定されていません。"
        )


    # --------------------------------------
    # 会話履歴
    # --------------------------------------

    conversation = ""

    if isinstance(history, list):

        conversation += "\nこれまでの会話:\n"

        for item in history[-20:]:

            if not isinstance(item, dict):
                continue

            role = item.get(
                "role",
                ""
            )

            text = item.get(
                "text",
                ""
            )

            if not text:
                continue

            if role == "user":

                conversation += (
                    "\nユーザー："
                    + str(text)
                )

            elif role == "assistant":

                conversation += (
                    "\nJ.A.R.V.I.S.："
                    + str(text)
                )


    conversation += (
        "\n\n今回のユーザーの発言：\n"
        + message
    )


    # --------------------------------------
    # Geminiへ送信
    # --------------------------------------

    for attempt in range(3):

        try:

            print("================================")
            print("J.A.R.V.I.S. REQUEST")
            print("MODEL:", MODEL)
            print("ATTEMPT:", attempt + 1)
            print("================================")


            response = client.models.generate_content(

                model=MODEL,

                contents=conversation,

                config=types.GenerateContentConfig(

                    system_instruction=SYSTEM_PROMPT,

                    temperature=0.7,

                    max_output_tokens=1000

                )

            )


            print("================================")
            print("J.A.R.V.I.S. RESPONSE RECEIVED")
            print("================================")


            reply = getattr(
                response,
                "text",
                None
            )


            if reply:

                return reply.strip()


            print(
                "Geminiからテキスト回答がありません"
            )

            return (
                "申し訳ありません、サー。"
                "回答を取得できませんでした。"
            )


        except Exception as e:

            error_type = type(e).__name__
            error_text = str(e)

            # APIキーそのものをログに出さない
            safe_error = error_text

            if API_KEY:
                safe_error = safe_error.replace(
                    API_KEY,
                    "[API_KEY_HIDDEN]"
                )


            print("")
            print("================================")
            print("J.A.R.V.I.S. GEMINI ERROR")
            print("TYPE:", error_type)
            print("ERROR:", safe_error)
            print("MODEL:", MODEL)
            print("ATTEMPT:", attempt + 1)
            print("================================")
            print("")


            # ----------------------------------
            # 503 / 429
            # ----------------------------------

            if (
                "503" in error_text
                or
                "UNAVAILABLE" in error_text
                or
                "429" in error_text
                or
                "RESOURCE_EXHAUSTED" in error_text
            ):

                if attempt < 2:

                    wait_time = 2 * (
                        attempt + 1
                    )

                    print(
                        "再試行します:",
                        wait_time,
                        "秒後"
                    )

                    time.sleep(
                        wait_time
                    )

                    continue


            # ----------------------------------
            # APIキー
            # ----------------------------------

            if (
                "401" in error_text
                or
                "UNAUTHENTICATED" in error_text
            ):

                return (
                    "申し訳ありません、サー。"
                    "Gemini APIキーを確認してください。"
                )


            # ----------------------------------
            # 権限
            # ----------------------------------

            if (
                "403" in error_text
                or
                "PERMISSION_DENIED" in error_text
            ):

                return (
                    "申し訳ありません、サー。"
                    "Gemini APIへのアクセス権限を"
                    "確認してください。"
                )


            # ----------------------------------
            # モデル
            # ----------------------------------

            if (
                "404" in error_text
                or
                "NOT_FOUND" in error_text
            ):

                return (
                    "申し訳ありません、サー。"
                    "Geminiモデルへの接続に失敗しました。"
                    "Renderのログをご確認ください。"
                )


            # ----------------------------------
            # その他
            # ----------------------------------

            return (
                "申し訳ありません、サー。"
                "Geminiとの通信中に"
                "エラーが発生しました。"
            )


    # ======================================
    # 3回失敗
    # ======================================

    return (
        "申し訳ありません、サー。"
        "現在Geminiサーバーが混雑しています。"
        "少し時間を置いて再度お試しください。"
    )


# ==========================================
# トップページ
# ==========================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ==========================================
# チャットAPI
# ==========================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    try:

        data = (
            request
            .get_json(
                silent=True
            )
            or {}
        )


        message = str(
            data.get(
                "message",
                ""
            )
        ).strip()


        history = data.get(
            "history",
            []
        )


        # ----------------------------------
        # 空メッセージ
        # ----------------------------------

        if not message:

            return jsonify({

                "success": False,

                "response":
                    "ご用件を入力してください、サー。",

                "error":
                    "empty_message"

            }), 400


        # ----------------------------------
        # 履歴
        # ----------------------------------

        if not isinstance(
            history,
            list
        ):

            history = []


        # ----------------------------------
        # Gemini
        # ----------------------------------

        reply = ask_gemini(
            message,
            history
        )


        # ----------------------------------
        # 返答
        # ----------------------------------

        return jsonify({

            "success": True,

            "response": reply,

            "error": False

        })


    except Exception as e:

        error_text = str(e)

        if API_KEY:
            error_text = error_text.replace(
                API_KEY,
                "[API_KEY_HIDDEN]"
            )


        print("================================")
        print("J.A.R.V.I.S. SERVER ERROR")
        print("TYPE:", type(e).__name__)
        print("ERROR:", error_text)
        print("================================")


        return jsonify({

            "success": False,

            "response":
                "申し訳ありません、サー。"
                "サーバー内部でエラーが発生しました。",

            "error":
                "server_error"

        }), 500


# ==========================================
# ヘルスチェック
# ==========================================

@app.route("/health")
def health():

    return jsonify({

        "status":
            "online",

        "assistant":
            "J.A.R.V.I.S.",

        "gemini":
            bool(client),

        "model":
            MODEL

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

        port=port,

        debug=False

    )
