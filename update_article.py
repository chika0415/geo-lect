import os
import json
import datetime
import google.generativeai as genai

# --- 1. 初期設定 ---
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.5-flash')

# --- 2. 時刻の準備 ---
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
display_date = now.strftime("%Y/%m/%d %H:%M")
date_id = now.strftime("%Y%m%d")

# --- 3. 記事・クイズ・銘柄生成プロンプト ---
prompt = f"""
最新の「世界政治」または「国際経済」のニュースから1つ選び、学習コンテンツをJSON形式で作成してください。
必ず以下の構造のJSONのみを出力してください：
{{
  "en_title": "英語見出し",
  "jp_title": "日本語見出し",
  "slug": "英語スラグ",
  "seo_description": "要約",
  "toeic_level": "推奨スコア (例: 700+)",
  "bg_gradient": "Tailwindグラデーション (例: from-blue-900 to-black)",
  "full_text_en": "読み上げ用全文",
  "segments": [{{"en": "英文", "jp": "和訳"}}],
  "stocks": [
    {{"name": "企業名", "code": "証券コード4桁"}}
  ],
  "quiz": [
    {{"q": "問題文(英語)", "options": ["A", "B", "C"], "ans": 0, "exp": "解説(日本語)"}}
  ],
  "advice": "専門的な戦略アドバイス",
  "vocab": [{{"w": "単語", "m": "意味"}}]
}}
"""

try:
    response = model.generate_content(prompt)
    raw_json = response.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(raw_json)

    # --- 4. データベース更新 ---
    os.makedirs("archive", exist_ok=True)
    db_file = "posts.json"
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            posts = json.load(f)
    else:
        posts = []
    
    new_slug = f"{date_id}-{data['slug']}"
    posts.insert(0, {"date_id": date_id, "title": data['en_title'], "url": f"archive/{new_slug}.html"})
    posts = posts[:15]
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    # --- 5. パーツ組み立て ---
    # 銘柄カード
    stocks_html = "".join([f"""
        <a href="https://jp.tradingview.com/symbols/TSE-{s['code']}/" target="_blank" class="block p-3 border rounded-xl hover:bg-slate-50 transition mb-2">
            <p class="text-[10px] font-bold text-blue-600">TSE: {s['code']}</p>
            <p class="text-xs font-black">{s['name']}</p>
        </a>""" for s in data['stocks']])

    # クイズ
    quiz_html = ""
    for i, q in enumerate(data['quiz']):
        options = "".join([f'<button onclick="checkQuiz({i}, {j})" class="block w-full text-left p-3 border rounded-lg text-sm mb-2 hover:bg-slate-50 transition">{opt}</button>' for j, opt in enumerate(q['options'])])
        quiz_html += f"""
        <div class="mb-8 p-6 bg-slate-50 rounded-2xl">
            <p class="font-bold mb-4">Q{i+1}. {q['q']}</p>
            <div id="q{i}-options">{options}</div>
            <p id="q{i}-exp" class="hidden text-xs text-slate-500 mt-4 pt-4 border-t italic">{q['exp']}</p>
        </div>"""

    # --- 6. 統合HTMLテンプレート ---
    full_html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['en_title']} | GEO-LECT Intelligence</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Playfair+Display:ital,wght@0,700;1,700&display=swap" rel="stylesheet">
    <style>
        :root {{ --bg: #f8fafc; --text: #0f172a; --card: #ffffff; --border: #e2e8f0; }}
        .dark {{ --bg: #0f172a; --text: #f1f5f9; --card: #1e293b; --border: #334155; }}
        body {{ background-color: var(--bg); color: var(--text); transition: 0.3s; font-family: 'Inter', sans-serif; }}
        .serif {{ font-family: 'Playfair Display', serif; }}
        .card {{ background-color: var(--card); border: 1px solid var(--border); }}
    </style>
</head>
<body class="antialiased pb-24">
    <header class="border-b border-slate-500/10 sticky top-0 z-50 backdrop-blur-lg bg-opacity-80 px-6 py-4 flex justify-between items-center">
        <h1 class="text-3xl font-black italic serif tracking-tighter">GEO-<span class="text-red-600">LECT</span></h1>
        <div class="flex items-center space-x-4">
            <span class="bg-blue-100 text-blue-700 text-[10px] font-black px-3 py-1 rounded-full border border-blue-200">TOEIC: {data['toeic_level']}</span>
            <button onclick="document.body.classList.toggle('dark')" class="p-2 border rounded-full text-xs font-bold uppercase">Mode</button>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-12">
        <div class="card rounded-3xl p-12 bg-gradient-to-br {data['bg_gradient']} mb-16 text-white shadow-2xl relative overflow-hidden">
            <div class="relative z-10">
                <div class="text-white/60 font-bold mb-4 tracking-widest text-[10px] uppercase">● {display_date} ANALYSIS</div>
                <h2 class="text-4xl md:text-6xl font-black mb-6 serif uppercase tracking-tighter leading-tight">{data['en_title']}</h2>
                <h3 class="text-2xl font-bold text-white/80 leading-snug serif">{data['jp_title']}</h3>
            </div>
        </div>

        <div class="grid lg:grid-cols-4 gap-12">
            <div class="lg:col-span-3 space-y-16">
                <div>{"".join([f'<div class="grid md:grid-cols-2 gap-10 pb-10 border-b border-slate-500/10"><div class="text-xl serif leading-relaxed">{s["en"]}</div><div class="text-lg opacity-70 italic border-l-4 border-red-600/30 pl-6 serif font-bold">{s["jp"]}</div></div>' for s in data['segments']])}</div>

                <div class="card rounded-3xl p-8 border-l-8 border-blue-600 bg-blue-600/5">
                    <h4 class="font-bold mb-3 text-blue-700 italic flex items-center tracking-tighter">🤖 STRATEGIC INSIGHT</h4>
                    <p class="leading-relaxed opacity-80 text-sm font-bold">{data['advice']}</p>
                </div>

                <section class="card rounded-3xl p-10 shadow-xl">
                    <h4 class="text-2xl font-bold mb-8 serif tracking-tighter uppercase border-b pb-4">Understanding Check</h4>
                    {quiz_html}
                </section>

                <div class="card rounded-3xl p-10 text-center shadow-xl border-2 border-dashed border-slate-200">
                    <h4 class="text-2xl font-bold mb-2 serif tracking-tighter uppercase">Pronunciation Analysis</h4>
                    <button id="recordBtn" onclick="toggleRecording()" class="mt-4 bg-red-600 text-white px-10 py-3 rounded-full font-black shadow-lg hover:scale-105 transition active:scale-95 text-xs uppercase">Start Recording</button>
                    <div id="feedback" class="mt-8 hidden p-6 bg-green-500/10 text-green-600 rounded-2xl font-bold text-sm">Perfect Accuracy! +15 STRAT-EXP</div>
                </div>

                <section class="mt-24">
                    <h4 class="font-bold mb-10 text-xs uppercase tracking-widest opacity-40 border-b pb-2 sans">Intelligence Archive</h4>
                    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                        {"".join([f'<a href="{p["url"] if "archive" in p["url"] else p["url"]}" class="group block card rounded-2xl p-5 border border-slate-700/10 hover:border-red-600 transition bg-white"><span class="text-[10px] text-slate-400 font-bold uppercase tracking-widest">{p["date_id"]}</span><h5 class="text-sm font-bold mt-1 group-hover:text-red-600 transition line-clamp-2 leading-tight serif">{p["title"]}</h5></a>' for p in posts[1:7]])}
                    </div>
                </section>
            </div>

            <aside class="space-y-8">
                <div class="card p-6 rounded-2xl shadow-sm">
                    <h4 class="font-bold mb-4 text-xs uppercase tracking-widest text-slate-400 border-b pb-2">Global Markets</h4>
                    <div class="space-y-4">
                        <div class="tradingview-widget-container">
                          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js" async>
                          {{
                            "colorTheme": "light", "dateRange": "12M", "showChart": false, "locale": "ja", "largeChartUrl": "", "isTransparent": true, "width": "100%", "height": "250",
                            "tabs": [ {{ "title": "Market", "symbols": [ {{ "s": "OANDA:USDJPY" }}, {{ "s": "INDEX:N225" }}, {{ "s": "INDEX:SPX" }}, {{ "s": "OANDA:XAUUSD" }} ] }} ]
                          }}
                          </script>
                        </div>
                    </div>
                </div>

                <div class="card p-6 rounded-2xl shadow-sm">
                    <h4 class="font-bold mb-4 text-xs uppercase tracking-widest text-red-600 border-b pb-2">Related Stocks</h4>
                    {stocks_html}
                </div>

                <div class="card p-6 rounded-2xl sticky top-24">
                    <h4 class="font-bold mb-6 text-xs uppercase tracking-widest text-blue-600 border-b pb-2 sans">Vocabulary</h4>
                    <ul class="space-y-6">{vocab_html}</ul>
                </div>
            </aside>
        </div>
    </main>

    <div class="fixed bottom-0 left-0 right-0 bg-slate-900 text-white p-4 z-50 border-t border-slate-700 backdrop-blur-md bg-opacity-90">
        <div class="max-w-4xl mx-auto flex items-center justify-between">
            <div class="hidden md:block truncate mr-4 text-[10px] font-bold uppercase tracking-widest opacity-50">Global Audio Stream</div>
            <div class="flex items-center space-x-8 mx-auto">
                <button id="playBtn" onclick="togglePlay()" class="bg-white text-slate-900 w-12 h-12 rounded-full flex items-center justify-center font-bold shadow-lg hover:scale-105 transition">▶</button>
            </div>
            <button onclick="resetAudio()" class="text-[10px] font-bold border border-white/20 px-3 py-1 rounded hover:bg-white/10">RESET</button>
        </div>
    </div>

    <script>
        const fullText = `{data['full_text_en'].replace('"', '\\"')}`;
        const quizData = {json.dumps(data['quiz'])};
        let speech = new SpeechSynthesisUtterance(fullText);
        speech.lang = 'en-US'; speech.rate = 0.9;
        let isPlaying = false;

        function togglePlay() {{
            const btn = document.getElementById('playBtn');
            if (!isPlaying) {{
                if (window.speechSynthesis.paused) window.speechSynthesis.resume();
                else window.speechSynthesis.speak(speech);
                btn.innerText = "II"; isPlaying = true;
            }} else {{
                window.speechSynthesis.pause();
                btn.innerText = "▶"; isPlaying = false;
            }}
        }}
        function resetAudio() {{ window.speechSynthesis.cancel(); isPlaying = false; document.getElementById('playBtn').innerText = "▶"; }}
        function checkQuiz(qIdx, optIdx) {{
            const correct = quizData[qIdx].ans;
            const exp = document.getElementById(`q${{qIdx}}-exp`);
            exp.classList.remove('hidden');
            if (optIdx === correct) alert("Correct! 🎯");
            else alert("Try again! ✍️");
        }}
        function toggleRecording() {{
            const btn = document.getElementById('recordBtn');
            btn.innerText = "LISTENING...";
            setTimeout(() => {{
                btn.innerText = "START RECORDING";
                document.getElementById('feedback').classList.remove('hidden');
            }}, 3000);
        }}
    </script>
</body>
</html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    
    archive_html = full_html.replace('href="archive/', 'href="')
    with open(f"archive/{new_slug}.html", "w", encoding="utf-8") as f:
        f.write(archive_html)

    sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\\n'
    sitemap += f'  <url><loc>https://chika0415.github.io/geo-lect/</loc></url>\\n'
    for p in posts:
        sitemap += f'  <url><loc>https://chika0415.github.io/geo-lect/{{p["url"]}}</loc></url>\\n'
    sitemap += '</urlset>'
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap)

    print(f"Success: {new_slug} created.")

except Exception as e:
    print(f"Error: {{e}}")
    exit(1)
