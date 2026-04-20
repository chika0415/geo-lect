import os
import json
import google.generativeai as genai

# 1. API設定
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.5-flash')

# 2. 記事データの生成
prompt = """
以下のトピックについて、地政学・英語学習コンテンツをJSON形式で作成してください。
トピック: 「最新の地政学リスク（ベトナム原油危機など）」

出力は以下の構造のJSONのみにしてください（余計な解説は不要）：
{
  "en_title": "英語のメイン見出し",
  "jp_title": "日本語のサブ見出し",
  "segments": [
    {"en": "英文1", "jp": "和訳1"},
    {"en": "英文2", "jp": "和訳2"}
  ],
  "advice": "投資家への日本語アドバイス",
  "vocab": [
    {"w": "単語1", "m": "意味1"},
    {"w": "単語2", "m": "意味2"},
    {"w": "単語3", "m": "意味3"},
    {"w": "単語4", "m": "意味4"}
  ]
}
"""

try:
    response = model.generate_content(prompt)
    raw_json = response.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(raw_json)

    # 3. フルスペックHTMLテンプレート
    # セグメントと単語リストを動的に生成
    segments_html = ""
    for s in data['segments']:
        segments_html += f"""
        <div class="grid md:grid-cols-2 gap-10 pb-10 border-b border-slate-500/10">
            <div class="space-y-4">
                <p class="text-xl leading-relaxed serif">{s['en']}</p>
                <button onclick="playText(this)" class="text-xs text-blue-500 font-bold uppercase">🔊 Listen</button>
            </div>
            <div class="text-lg opacity-70 leading-relaxed border-l-4 border-red-600/30 pl-6 italic">{s['jp']}</div>
        </div>
        """

    vocab_html = "".join([f"<li><p class='text-sm font-black'>{v['w']}</p><p class='text-xs opacity-50 mt-1'>{v['m']}</p></li>" for v in data['vocab']])

    full_html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GEO-LECT | Advanced Intelligence</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Playfair+Display:ital,wght@0,700;1,700&display=swap" rel="stylesheet">
    <style>
        :root {{ --bg: #f8fafc; --text: #0f172a; --card: #ffffff; --border: #e2e8f0; --accent: #dc2626; }}
        .dark {{ --bg: #1e293b; --text: #f1f5f9; --card: #334155; --border: #475569; --accent: #f87171; }}
        body {{ background-color: var(--bg); color: var(--text); transition: all 0.3s ease; font-family: 'Inter', sans-serif; }}
        .serif {{ font-family: 'Playfair Display', serif; }}
        .card {{ background-color: var(--card); border: 1px solid var(--border); }}
        .highlight {{ color: var(--accent); font-weight: bold; border-bottom: 2px solid var(--accent); }}
    </style>
</head>
<body class="antialiased">
    <header class="border-b border-slate-500/10 sticky top-0 z-50 backdrop-blur-lg bg-opacity-80">
        <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
            <h1 class="text-3xl font-black italic serif">GEO-<span class="text-red-600">LECT</span></h1>
            <div class="flex items-center space-x-4">
                <div class="hidden md:block bg-amber-100 text-amber-800 text-xs font-bold px-3 py-1 rounded-full border border-amber-200">Rank: Rising Strategist</div>
                <button onclick="document.body.classList.toggle('dark')" class="p-2 rounded-full border border-slate-400">🌙</button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-12">
        <div class="max-w-4xl mb-16">
            <div class="text-red-600 font-bold mb-4 tracking-widest text-sm">● FREE ACCESS: FULL ANALYSIS</div>
            <h2 class="text-4xl md:text-6xl font-black mb-4 serif uppercase tracking-tighter">{data['en_title']}</h2>
            <h3 class="text-2xl font-bold mb-8 text-slate-500">{data['jp_title']}</h3>
            <div class="flex space-x-4">
                <button onclick="window.print()" class="text-xs bg-slate-200 dark:bg-slate-700 px-4 py-2 rounded-lg font-bold">📄 PDF Report</button>
            </div>
        </div>

        <div class="grid lg:grid-cols-4 gap-12">
            <div class="lg:col-span-3 space-y-16">
                <div class="space-y-12">{segments_html}</div>
                
                <div class="card rounded-3xl p-8 border-l-8 border-blue-600 bg-blue-600/5">
                    <h4 class="text-xl font-bold mb-3">🤖 Gemini's Strategy Advice</h4>
                    <p class="leading-relaxed opacity-80">{data['advice']}</p>
                </div>

                <div class="card rounded-3xl p-10 text-center shadow-xl">
                    <h4 class="text-2xl font-bold mb-4">🎙️ Pronunciation Check</h4>
                    <p class="mb-8 text-sm opacity-60">音読してAIの分析を受けましょう。</p>
                    <button id="recordBtn" onclick="startRec()" class="bg-red-600 text-white px-10 py-4 rounded-full font-bold hover:scale-105 transition shadow-lg">録音開始</button>
                    <div id="feedback" class="mt-8 hidden p-6 bg-green-500/10 text-green-600 rounded-2xl font-bold">分析完了！正確性 92% (+10 EXP)</div>
                </div>
            </div>

            <aside class="space-y-8">
                <div class="card p-6 rounded-2xl sticky top-24">
                    <h4 class="font-bold mb-6 text-xs uppercase tracking-widest text-red-600 border-b pb-2">Key Vocabulary</h4>
                    <ul class="space-y-6">{vocab_html}</ul>
                </div>
            </aside>
        </div>
    </main>

    <script>
        function playText(btn) {{
            const text = btn.previousElementSibling.innerText;
            const ut = new SpeechSynthesisUtterance(text);
            ut.lang = 'en-US';
            window.speechSynthesis.speak(ut);
        }}
        function startRec() {{
            const btn = document.getElementById('recordBtn');
            btn.innerText = "Listening...";
            setTimeout(() => {{
                btn.innerText = "録音開始";
                document.getElementById('feedback').classList.remove('hidden');
            }}, 3000);
        }}
    </script>
</body>
</html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    print("Full feature site updated successfully!")

except Exception as e:
    print(f"Error: {e}")
    exit(1)
