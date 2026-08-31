import os
import time

from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types


# =========================================================
# Flask
# =========================================================

app = Flask(__name__)


# =========================================================
# Gemini
# =========================================================

API_KEY = os.environ.get("GEMINI_API_KEY")

# 現在使用するGeminiモデル
MODEL = "gemini-3.7-flash"

client = None

if API_KEY:
    client = genai.Client(
        api_key=API_KEY
    )


# =========================================================
# J.A.R.V.I.S. SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
あなたはJ.A.R.V.I.S.です。

ユーザーを「サー」と呼んでください。

あなたはユーザー専用のAIアシスタントです。

【話し方】
・丁寧な日本語
・落ち着いた口調
・自然な会話
・優秀なAI執事のような雰囲気
・必要以上に長く説明しない
・質問には分かりやすく具体的に答える

【重要】
ユーザーが普通に話しかけた場合は、
普通の会話として自然に返答してください。

音声機能について質問されていない場合、
音声機能について勝手に説明しないでください。

「現在テキストのみです」
「音声には対応していません」
などの説明を勝手に出さないでください。

ユーザーから質問や指示があれば、
可能な限り役に立つ回答をしてください。

あなたの名前はJ.A.R.V.I.S.です。
"""


# =========================================================
# Geminiへ問い合わせ
# =========================================================

def ask_gemini(message, history=None):

    # -----------------------------------------------------
    # APIキー確認
    # -----------------------------------------------------

    if not API_KEY:

        print("====================================")
        print("J.A.R.V.I.S. ERROR")
        print("GEMINI_API_KEY が設定されていません")
        print("====================================")

        return (
            "申し訳ありません、サー。"
            "Gemini APIキーが設定されていません。"
        )


    # -----------------------------------------------------
    # 会話を作成
    # -----------------------------------------------------

    conversation = ""

    if isinstance(history, list):

        conversation += "\n【これまでの会話】\n"

        # 最新20件まで
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
        "\n\n【今回の発言】\n"
        + message
    )


    # -----------------------------------------------------
    # Gemini API
    # -----------------------------------------------------

    for attempt in range(3):

        try:

            print("")
            print("====================================")
            print("J.A.R.V.I.S. REQUEST")
            print("MODEL:", MODEL)
            print("ATTEMPT:", attempt + 1)
            print("====================================")


            response = client.models.generate_content(

                model=MODEL,

                contents=conversation,

                config=types.GenerateContentConfig(

                    system_instruction=SYSTEM_PROMPT,

                    max_output_tokens=2000

                )
            )


            # ------------------------------------------------
            # 回答取得
            # ------------------------------------------------

            reply = getattr(
                response,
                "text",
                None
            )


            if reply:

                print("====================================")
                print("J.A.R.V.I.S. RESPONSE OK")
                print("====================================")

                return reply.strip()


            print(
                "Geminiからテキストが返されませんでした。"
            )

            return (
                "申し訳ありません、サー。"
                "回答を取得できませんでした。"
            )


        except Exception as e:

            error_type = type(e).__name__
            error_text = str(e)


            # APIキーをログに出さない
            safe_error = error_text

            if API_KEY:

                safe_error = safe_error.replace(
                    API_KEY,
                    "[API_KEY_HIDDEN]"
                )


            print("")
            print("====================================")
            print("J.A.R.V.I.S. GEMINI ERROR")
            print("TYPE:", error_type)
            print("ERROR:", safe_error)
            print("MODEL:", MODEL)
            print("ATTEMPT:", attempt + 1)
            print("====================================")
            print("")


            # ------------------------------------------------
            # サーバー混雑 / レート制限
            # ------------------------------------------------

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

                    wait_time = (
                        2 ** attempt
                    )

                    print(
                        "Geminiサーバーが混雑しています。"
                    )

                    print(
                        wait_time,
                        "秒後に再試行します。"
                    )

                    time.sleep(
                        wait_time
                    )

                    continue


                return (
                    "申し訳ありません、サー。"
                    "現在Geminiサーバーが混雑しています。"
                    "少し時間を置いて再度お試しください。"
                )


            # ------------------------------------------------
            # APIキーエラー
            # ------------------------------------------------

            if (
                "401" in error_text
                or
                "UNAUTHENTICATED" in error_text
            ):

                return (
                    "申し訳ありません、サー。"
                    "Gemini APIキーが正しくありません。"
                    "RenderのGEMINI_API_KEYを確認してください。"
                )


            # ------------------------------------------------
            # 権限エラー
            # ------------------------------------------------

            if (
                "403" in error_text
                or
                "PERMISSION_DENIED" in error_text
            ):

                return (
                    "申し訳ありません、サー。"
                    "Gemini APIへのアクセス権限を確認してください。"
                )


            # ------------------------------------------------
            # モデルが見つからない
            # ------------------------------------------------

            if (
                "404" in error_text
                or
                "NOT_FOUND" in error_text
            ):

                return (
                    "申し訳ありません、サー。"
                    "指定したGeminiモデルが利用できません。"
                    "Renderのログをご確認ください。"
                )


            # ------------------------------------------------
            # その他
            # ------------------------------------------------

            return (
                "申し訳ありません、サー。"
                "Geminiとの通信中にエラーが発生しました。"
            )


    # -----------------------------------------------------
    # 全試行失敗
    # -----------------------------------------------------

    return (
        "申し訳ありません、サー。"
        "Geminiとの通信に失敗しました。"
        "少し時間を置いて再度お試しください。"
    )


# =========================================================
# トップページ
# =========================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# =========================================================
# チャット
# =========================================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    try:

        data = (
            request.get_json(
                silent=True
            )
            or {}
        )


        # --------------------------------------------------
        # メッセージ
        # --------------------------------------------------

        message = str(
            data.get(
                "message",
                ""
            )
        ).strip()


        # --------------------------------------------------
        # 会話履歴
        # --------------------------------------------------

        history = data.get(
            "history",
            []
        )


        if not isinstance(
            history,
            list
        ):

            history = []


        # --------------------------------------------------
        # 空メッセージ
        # --------------------------------------------------

        if not message:

            return jsonify({

                "success": False,

                "response":
                    "ご用件を入力してください、サー。",

                "error":
                    "empty_message"

            }), 400


        # --------------------------------------------------
        # Gemini
        # --------------------------------------------------

        reply = ask_gemini(
            message,
            history
        )


        # --------------------------------------------------
        # 返答
        # --------------------------------------------------

        return jsonify({

            "success": True,

            "response": reply,

            "error": None

        })


    except Exception as e:

        error_text = str(e)

        if API_KEY:

            error_text = error_text.replace(
                API_KEY,
                "[API_KEY_HIDDEN]"
            )


        print("")
        print("====================================")
        print("J.A.R.V.I.S. SERVER ERROR")
        print("TYPE:", type(e).__name__)
        print("ERROR:", error_text)
        print("====================================")
        print("")


        return jsonify({

            "success": False,

            "response":
                "申し訳ありません、サー。"
                "サーバー内部でエラーが発生しました。",

            "error":
                "server_error"

        }), 500


# =========================================================
# Health Check
# =========================================================

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


# =========================================================
# 起動
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )


    print("")
    print("====================================")
    print("J.A.R.V.I.S. STARTING")
    print("MODEL:", MODEL)
    print("PORT:", port)
    print("GEMINI API:", bool(API_KEY))
    print("====================================")
    print("")


    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )
