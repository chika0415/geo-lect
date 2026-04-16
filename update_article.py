import os
import google.generativeai as genai

# 1. まずAPIキーを設定（これは必須！）
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# 2. ここでデバッグ用のコードを入れる
print("--- 利用可能なモデル一覧 ---")
for m in genai.list_models():
    print(m.name)
print("---------------------------")

# 3. モデルの指定（エラーが出る場合は、上のログに出た名前に書き換える）
# 2026年現在、'models/gemini-1.5-flash-latest' や 'models/gemini-2.0-flash' 
# などが候補になります。
try:
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    # 記事生成のプロンプト
    prompt = "ベトナムの原油危機をテーマに、英語・日本語の見出し、対訳、重要単語リストをHTML形式で作成して。"
    response = model.generate_content(prompt)

    # index.htmlに書き込み
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("記事の更新に成功しました！")

except Exception as e:
    print(f"エラーが発生しました: {e}")
