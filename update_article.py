import os
import google.generativeai as genai

# 1. API設定
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.5-flash')

# 2. Geminiに「記事データだけ」を生成させる（HTML全体ではなく）
prompt = """
以下のトピックについて、英語学習用のコンテンツを「JSON形式」で作成してください。
トピック: ベトナムのエネルギー危機と地政学リスク

出力は必ず以下の項目を含むJSONのみにしてください：
{
  "en_title": "英語の見出し",
  "jp_title": "日本語の見出し",
  "en_1": "英語の1文目",
  "jp_1": "日本語の1文目",
  "en_2": "英語の2文目",
  "jp_2": "日本語の2文目",
  "advice": "投資家への日本語アドバイス",
  "vocab": [{"w": "単語1", "m": "意味1"}, {"w": "単語2", "m": "意味2"}]
}
"""

try:
    response = model.generate_content(prompt)
    # JSON部分だけを抽出
    raw_json = response.text.replace("```json", "").replace("```", "").strip()
    import json
    data = json.loads(raw_json)

    # 3. 高級デザインのHTMLテンプレート（ここにデータを埋め込む）
    html_template = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><title>GEO-LECT</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        :root {{ --bg: #f8fafc; --text: #0f172a; --card: #ffffff; --border: #e2e8f0; }}
        .dark {{ --bg: #1e293b; --text: #f1f5f9; --card: #334155; --border: #475569; }}
        body {{ background-color: var(--bg); color: var(--text); transition: all 0.3s; font-family: 'Inter', sans-serif; }}
        .card {{ background-color: var(--card); border: 1px solid var(--border); }}
    </style>
</head>
<body class="antialiased">
    <header class="border-b border-slate-500/10 p-6 flex justify-between items-center">
        <h1 class="text-3xl font-black italic">GEO-<span class="text-red-600">LECT</span></h1>
        <button onclick="document.body.classList.toggle('dark')" class="p-2 border rounded-full">🌙/☀️</button>
    </header>
    <main class="max-w-6xl mx-auto px-6 py-12">
        <div class="mb-12">
            <h2 class="text-5xl font-bold mb-4">{data['en_title']}</h2>
            <h3 class="text-2xl font-bold text-slate-500">{data['jp_title']}</h3>
        </div>
        <div class="grid lg:grid-cols-3 gap-12">
            <div class="lg:col-span-2 space-y-12">
                <div class="grid md:grid-cols-2 gap-8 border-b pb-8">
                    <div class="text-xl leading-relaxed">{data['en_1']}</div>
                    <div class="text-lg opacity-60 italic border-l-4 border-red-600/30 pl-6">{data['jp_1']}</div>
                </div>
                <div class="grid md:grid-cols-2 gap-8 border-b pb-8">
                    <div class="text-xl leading-relaxed">{data['en_2']}</div>
                    <div class="text-lg opacity-60 italic border-l-4 border-red-600/30 pl-6">{data['jp_2']}</div>
                </div>
                <div class="card p-8 rounded-3xl border-l-8 border-blue-600">
                    <h4 class="font-bold mb-2">🤖 Gemini's Strategy</h4>
                    <p>{data['advice']}</p>
                </div>
            </div>
            <aside class="card p-6 rounded-2xl h-fit">
                <h4 class="font-bold mb-4 text-red-600">Key Vocabulary</h4>
                <ul class="space-y-4">
                    {"".join([f"<li><p class='font-bold'>{v['w']}</p><p class='text-xs opacity-50'>{v['m']}</p></li>" for v in data['vocab']])}
                </ul>
            </aside>
        </div>
    </main>
</body>
</html>
    """

    # 4. 完成したHTMLを保存
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("Successfully updated with template!")

except Exception as e:
    print(f"Error: {e}")
    exit(1)
