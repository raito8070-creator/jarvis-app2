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

ユーザーのことを必ず「サー」と呼んでください。

話し方：
- 丁寧
- 冷静
- 自然な日本語
- 優秀なAI執事のように話す
- 必要以上に長くしない
- 質問には具体的に答える
- 分からないことは正直に伝える

重要：
ユーザーが音声について質問していない限り、
音声機能について説明しないでください。

「現在テキストのみです」
「音声には対応していません」
「端末の読み上げ機能を使ってください」
などの説明を勝手にしないでください。

あなたはJ.A.R.V.I.S.として、
ユーザーをサポートしてください。
"""


# ==========================================
# Geminiへ問い合わせ
# ==========================================

def ask_gemini(message, history=None):

    if client is None:

        print("ERROR: GEMINI_API_KEY がありません")

        return (
            "申し訳ありません、サー。"
            "Gemini APIキーが設定されていません。"
        )


    # --------------------------------------
    # 会話を作成
    # --------------------------------------

    conversation = ""


    if history:

        conversation += "\nこれまでの会話:\n"

        for item in history[-20:]:

            if not isinstance(item, dict):
                continue

            role = item.get("role", "")
            text = item.get("text", "")

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


            # ----------------------------------
            # 回答取得
            # ----------------------------------

            reply = getattr(
                response,
                "text",
                None
            )


            if reply:

                return reply.strip()


            print(
                "WARNING: Geminiから"
                "テキスト回答がありません"
            )


            return (
                "申し訳ありません、サー。"
                "回答を取得できませんでした。"
            )


        except Exception as e:

            error_type = type(e).__name__
            error_text = str(e)


            print("================================")
            print("J.A.R.V.I.S. GEMINI ERROR")
            print("TYPE:", error_type)
            print("ERROR:", error_text)
            print("================================")


            # ----------------------------------
            # 一時的なエラーなら再試行
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
                        "Retrying in",
                        wait_time,
                        "seconds..."
                    )

                    time.sleep(
                        wait_time
                    )

                    continue


            # ----------------------------------
            # その他のエラー
            # ----------------------------------

            if "401" in error_text:

                return (
                    "申し訳ありません、サー。"
                    "Gemini APIキーが正しくありません。"
                )


            if "403" in error_text:

                return (
                    "申し訳ありません、サー。"
                    "Gemini APIへのアクセスが"
                    "許可されていません。"
                )


            if "404" in error_text:

                return (
                    "申し訳ありません、サー。"
                    "指定したGeminiモデルが"
                    "利用できません。"
                )


            if (
                "429" in error_text
                or
                "RESOURCE_EXHAUSTED"
                in error_text
            ):

                return (
                    "申し訳ありません、サー。"
                    "Gemini APIの利用上限に"
                    "達している可能性があります。"
                )


            # ----------------------------------
            # 不明なエラー
            # ----------------------------------

            return (
                "申し訳ありません、サー。"
                "Geminiとの通信中に"
                "エラーが発生しました。"
            )


    # --------------------------------------
    # 3回失敗
    # --------------------------------------

    return (
        "申し訳ありません、サー。"
        "現在AIサーバーが混雑しています。"
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
# チャット
# ==========================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    try:

        # ----------------------------------
        # JSON取得
        # ----------------------------------

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
        # 履歴チェック
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

        print("================================")
        print("J.A.R.V.I.S. SERVER ERROR")
        print(type(e).__name__)
        print(str(e))
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
