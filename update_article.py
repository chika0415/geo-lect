import os
import google.generativeai as genai

# Geminiの設定
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
# それでもダメなら Pro 版を試す
model = genai.GenerativeModel('gemini-1.5-pro')

# Geminiへの指示（ここで内容をコントロールします）
prompt = """
以下の条件で、最新の地政学・経済ニュースに基づいた英語学習コンテンツを作成してください。
トピック: ベトナムのエネルギー危機と地政学リスク
条件: 英語と日本語の対訳を3つ、重要単語4つ。
出力形式: そのままHTMLの <div id="articleContent">〜</div> の中身として使える形式で。
見出し（日米）も含めて。
"""

response = model.generate_content(prompt)

# HTMLファイルの読み込み
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# ここで「前回の記事」を「新しい記事」に置換する処理を入れます
# （簡易的な実装として、特定のタグの間を入れ替える仕組み）
# ※最初はGeminiにHTML全文を再生成させるのが一番簡単です
with open("index.html", "w", encoding="utf-8") as f:
    f.write(response.text) # GeminiにHTMLをまるごと出力させる設定
