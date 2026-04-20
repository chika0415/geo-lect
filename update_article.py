import os
import json
import datetime
import google.generativeai as genai

# 1. API設定
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.5-flash')

# 2. 現在時刻の取得
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
timestamp = now.strftime("%Y%m%d_%H%M")
display_date = now.strftime("%Y/%m/%d %H:%M")

# 3. 記事データの生成
prompt = f"""
以下のトピックについて、地政学・英語学習コンテンツをJSON形式で作成してください。
トピック: 「最新の地政学・経済リスク」
日付: {display_date}

必ず以下の構造のJSONのみを出力してください：
{{
  "en_title": "英語メイン見出し",
  "jp_title": "日本語サブ見出し",
  "segments": [
    {{"en": "英文1", "jp": "和訳1"}},
    {{"en": "英文2", "jp": "和訳2"}}
  ],
  "advice": "投資アドバイス",
  "vocab": [
    {{"w": "単語1", "m": "意味1"}},
    {{"w": "単語2", "m": "意味2"}},
    {{"w": "単語3", "m": "意味3"}},
    {{"w": "単語4", "m": "意味4"}}
  ]
}}
"""

try:
    response = model.generate_content(prompt)
    raw_json = response.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(raw_json)

    # 4. アーカイブフォルダの準備とリンク作成
    os.makedirs("archive", exist_ok=True)
    past_articles = [f for f in os.listdir("archive") if f.endswith(".html")]
    past_articles.sort(reverse=True)
    archive_links_html = "".join([f'<li><a href="archive/{f}" class="text-blue-500 hover:underline text-sm">{f[:8]} の分析</a></li>' for f in past_articles[:5]])

    # 5. HTMLコンテンツの組み立て
    segments_html = "".join([f"""
        <div class="grid md:grid-cols-2 gap-10 pb-10 border-b border-slate-500/10">
            <div class="space-y-4">
                <p class="text-xl leading-relaxed serif">{s['en']}</p>
                <button onclick="playText(this)" class="text-xs text-blue-500 font-bold uppercase">🔊 Listen</button>
            </div>
            <div class="text-lg opacity-70 leading-relaxed border-l-4 border-red-600/30 pl-6 italic">{s['jp']}</div>
        </div>
    """ for s in data['segments']])

    vocab_html = "".join([f"<li><p class='text-sm font-black'>{v['w']}</p><p class='text-xs opacity-50 mt-1'>{v['m']}</p></li>" for v in data['vocab']])

    # 6. フルスペックHTMLテンプレート（CSSやJSの {{ }} は Python f-string 用に2重にする必要あり）
    full_html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GEO-LECT | {display_date}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Playfair+Display:ital,wght@0,700;1,700&display=swap" rel="stylesheet">
    <style>
        :root {{ --bg: #f8fafc; --text: #0f172a; --card: #ffffff; --border: #e2e8f0; --accent: #dc2626; }}
        .dark {{ --bg: #1e293b; --text: #f1f5f9; --card: #334155; --border: #475569; --accent: #f87171; }}
        body {{ background-color: var(--bg); color: var(--text); transition: all 0.3s ease; font-family: 'Inter', sans-serif; }}
        .serif {{ font-family: 'Playfair Display', serif; }}
        .card {{ background-color: var(--card); border: 1px solid var(--border); }}
    </style>
</head>
<body class="antialiased">
    <header class="border-b border-slate-500/10 sticky top-0 z-50 backdrop-blur-lg bg-opacity-80">
        <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
            <h1 class="text-3xl font-black italic serif">GEO-<span class="text-red-600">LECT</span></h1>
            <div class="flex items-center space-x-4">
                <button onclick="document.body.classList.toggle('dark')" class="p-2 rounded-full border border-slate-400">🌙</button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-12">
        <div class="max-w-4xl mb-16">
            <div class="text-red-600 font-bold mb-4 tracking-widest text-sm">● {display_date} UPDATE</div>
            <h2 class="text-4xl md:text-6xl font-black mb-4 serif uppercase tracking-tighter">{data['en_title']}</h2>
            <h3 class="text-2xl font-bold mb-8 text-slate-500">{data['jp_title']}</h3>
        </div>

        <div class="grid lg:grid-cols-4 gap-12">
            <div class="lg:col-span-3 space-y-16">
                <div class="space-y-12">{segments_html}</div>
                
                <div class="card rounded-3xl p-8 border-l-8 border-blue-600 bg-blue-600/5">
                    <h4 class="text-xl font-bold mb-3">🤖 Gemini's Strategy Insight</h4>
                    <p class="leading-relaxed opacity-80">{data['advice']}</p>
                </div>

                <div class="card rounded-3xl p-10 text-center shadow-xl">
                    <h4 class="text-2xl font-bold mb-4">🎙️ Pronunciation Trainer</h4>
                    <button id="recordBtn" onclick="startRec()" class="bg-red-600 text-white px-10 py-4 rounded-full font-bold shadow-lg transition hover:scale-105">録音開始</button>
                    <div id="feedback" class="mt-8 hidden p-6 bg-green-500/10 text-green-600 rounded-2xl font-bold">Good Job! Accurate pronunciation detected.</div>
                </div>

                <section class="p-8 card rounded-3xl bg-slate-100 dark:bg-slate-800/50 mt-12">
                    <h4 class="font-bold mb-4 text-xs uppercase tracking-widest opacity-50 border-b pb-2">Archive | 過去の分析記事</h4>
                    <ul class="grid grid-cols-1 md:grid-cols-2 gap-2">{archive_links_html}</ul>
                </section>
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

    # 保存処理
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    
    archive_filename = f"archive/{timestamp}.html"
    with open(archive_filename, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"Full Update & Archive Success: {archive_filename}")

except Exception as e:
    print(f"Error: {e}")
    exit(1)
