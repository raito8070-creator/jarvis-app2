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

    return jsonify({

        "reply": (
            "申し訳ありません、サー。\n"
            "AIとの通信中にエラーが発生しました。"
        ),

        "error": True

    })
