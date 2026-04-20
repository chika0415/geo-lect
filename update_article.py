import os
import google.generativeai as genai

# APIキー設定
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# リストにあった「確実に存在するモデル名」を使用します
model_name = 'models/gemini-2.5-flash' 
print(f"Using model: {model_name}")

# モデルの起動
model = genai.GenerativeModel(model_name)

# 記事生成（HTML形式で出力させる）
prompt = """
以下の条件で、最新の地政学・経済ニュースに基づいた英語学習コンテンツをHTML形式で作成してください。
トピック: ベトナムのエネルギー危機と地政学リスク
条件: 
1. 英語の見出しと日本語の見出しを併記。
2. 英語と日本語の対訳を3つ。
3. 重要単語リスト。
出力形式: そのまま index.html として保存可能な完全なHTML形式で（CSSも含めて）。
"""

try:
    response = model.generate_content(prompt)
    
    # ファイル書き出し
    with open("index.html", "w", encoding="utf-8") as f:
        # Geminiの回答からコードブロックの記号（```html ... ```）を掃除して保存
        content = response.text.replace("```html", "").replace("```", "").strip()
        f.write(content)
        
    print("Successfully wrote index.html!")

except Exception as e:
    print(f"Error during content generation: {e}")
    # エラーが起きた場合は、わざと異常終了させてGitHubに知らせる
    exit(1)
