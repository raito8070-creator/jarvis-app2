# J.A.R.V.I.S. All-in-One

追加済み:
- Geminiチャット
- 会話履歴（ブラウザ保存）
- 音声入力（対応ブラウザ）＋iPhoneキーボード音声入力へのフォールバック
- AI回答の音声読み上げ
- Google検索ツールON/OFF
- 画像アップロード＋画像解析
- PDF/TXT/MD/CSVアップロード＋解析
- J.A.R.V.I.S.風UI
- /health システム状態

## Render
Build Command:
`pip install -r requirements.txt`

Start Command:
`gunicorn app:app`

Environment Variables:
- `GEMINI_API_KEY` = Google AI StudioのAPIキー
- `GEMINI_MODEL` = `gemini-2.5-flash`

APIキーはGitHubのコードに書かないでください。
RenderのEnvironment Variablesに設定してください。
