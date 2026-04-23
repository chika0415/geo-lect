import os
import json
import datetime
import google.generativeai as genai

# --- 1. API設定 ---
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.5-flash')

# --- 2. 時刻の準備 ---
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
display_date = now.strftime("%Y/%m/%d %H:%M")
date_id = now.strftime("%Y%m%d")

# --- 3. 記事・クイズ・銘柄生成プロンプト (政治・経済全般) ---
prompt = f"""
最新の「世界政治」または「国際経済」のニュースから1つ選び、学習コンテンツを作成してください。
以下のJSON形式のみを出力してください（余計な解説は一切不要）：
{{
  "en_title": "英語見出し",
  "jp_title": "日本語見出し",
  "slug": "英語スラグ (例: fed-interest-rate-hike)",
  "seo_description": "100文字程度の要約",
  "toeic_level": "推奨スコア (例: 800+)",
  "bg_gradient": "Tailwindグラデーション (例: from-slate-900 to-indigo-900)",
  "full_text_en": "読み上げ用の全英文テキスト",
  "segments": [{{ "en": "英文1", "jp": "和訳1" }}, {{ "en": "英文2", "jp": "和訳2" }}],
  "stocks": [{{ "name": "関連日本企業名", "code": "証券コード4桁" }}],
  "quiz": [{{ "q": "問題(英語)", "options": ["A", "B", "C"], "ans": 0, "exp": "解説" }}],
  "advice": "投資・戦略アドバイス (日本語)",
  "vocab": [{{ "w": "単語", "m": "意味" }}]
}}
"""

try:
    response = model.generate_content(prompt)
    raw_json = response.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(raw_json)

    # 4. データベース更新
    os.makedirs("archive", exist_ok=True)
    db_file = "posts.json"
    posts = json.load(open(db_file, "r", encoding="utf-8")) if os.path.exists(db_file) else []
    new_slug = f"{date_id}-{data['slug']}"
    posts.insert(0, {"date_id": date_id, "title": data['en_title'], "url": f"archive/{new_slug}.html"})
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(posts[:15], f, ensure_ascii=False, indent=2)

    # 5. パーツ組み立て
    stocks_html = "".join([f'<a href="https://jp.tradingview.com/symbols/TSE-{s["code"]}/" target="_blank" class="block p-3 border rounded-xl hover:bg-slate-50 mb-2"><p class="text-[10px] font-bold text-blue-600">TSE: {s["code"]}</p><p class="text-xs font-black">{s["name"]}</p></a>' for s in data['stocks']])
    
    quiz_json_js = json.dumps(data['quiz'], ensure_ascii=False)
    full_text_js = json.dumps(data['full_text_en'], ensure_ascii=False)
    
    quiz_html = ""
    for i, q in enumerate(data['quiz']):
        opts = "".join([f'<button onclick="checkQuiz({i}, {j})" class="block w-full text-left p-3 border rounded-lg text-sm hover:bg-white transition">{opt}</button>' for j, opt in enumerate(q['options'])])
        quiz_html += f'<div class="mb-8 p-6 bg-slate-50 dark:bg-slate-800/50 rounded-2xl"><p class="font-bold mb-4">Q{i+1}. {q["q"]}</p><div class="space-y-2">{opts}</div><p id="q{i}-exp" class="hidden text-xs text-slate-500 mt-4 pt-4 border-t italic">{q["exp"]}</p></div>'

    # 6. HTMLテンプレート
    full_html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['en_title']} | GEO-LECT</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <style>
        :root {{ --bg: #f8fafc; --text: #0f172a; --card: #ffffff; }}
        .dark {{ --bg: #0f172a; --text: #f1f5f9; --card: #1e293b; }}
        body {{ background-color: var(--bg); color: var(--text); transition: 0.3s; font-family: 'Inter', sans-serif; }}
        .serif {{ font-family: 'Playfair Display', serif; }}
        .card {{ background-color: var(--card); border: 1px solid #e2e8f0; }}
    </style>
</head>
<body class="antialiased pb-32">
    <header class="border-b sticky top-0 z-40 backdrop-blur-lg bg-opacity-80 px-6 py-4 flex justify-between items-center">
        <h1 class="text-3xl font-black italic serif">GEO-<span class="text-red-600">LECT</span></h1>
        <div class="flex items-center space-x-4">
            <span class="bg-blue-100 text-blue-700 text-[10px] font-black px-3 py-1 rounded-full border border-blue-200">TOEIC {data['toeic_level']}</span>
            <button onclick="document.body.classList.toggle('dark')" class="p-2 border rounded-full text-xs font-bold">MODE</button>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-12">
        <div class="card rounded-3xl p-12 bg-gradient-to-br {data['bg_gradient']} mb-16 text-white shadow-2xl">
            <div class="text-white/60 font-bold mb-4 tracking-widest text-[10px] uppercase">● {display_date} ANALYSIS</div>
            <h2 class="text-4xl md:text-6xl font-black mb-6 serif uppercase tracking-tighter leading-tight">{data['en_title']}</h2>
            <h3 class="text-2xl font-bold text-white/80 leading-snug serif">{data['jp_title']}</h3>
        </div>

        <div class="grid lg:grid-cols-4 gap-12">
            <div class="lg:col-span-3 space-y-16">
                <div>{"".join([f'<div class="grid md:grid-cols-2 gap-10 pb-10 border-b mb-10"><div class="text-xl serif leading-relaxed">{s["en"]}</div><div class="text-lg opacity-70 italic border-l-4 border-red-600/30 pl-6 font-bold">{s["jp"]}</div></div>' for s in data['segments']])}</div>
                
                <div class="card rounded-3xl p-8 border-l-8 border-blue-600 bg-blue-600/5">
                    <h4 class="font-bold mb-3 text-blue-700 italic flex items-center">🤖 STRATEGIC INSIGHT</h4>
                    <p class="leading-relaxed opacity-80 text-sm font-bold">{data['advice']}</p>
                </div>

                <section class="card rounded-3xl p-10 shadow-xl">
                    <h4 class="text-2xl font-bold mb-8 serif tracking-tighter uppercase border-b pb-4">Understanding Check</h4>
                    {quiz_html}
                </section>

                <div class="card rounded-3xl p-10 text-center shadow-xl border-2 border-dashed">
                    <h4 class="text-2xl font-bold mb-2 serif uppercase tracking-tighter">Pronunciation Analysis</h4>
                    <button id="recordBtn" onclick="toggleRec()" class="mt-4 bg-red-600 text-white px-10 py-3 rounded-full font-black text-xs uppercase">Start Recording</button>
                    <div id="feedback" class="mt-8 hidden p-6 bg-green-500/10 text-green-600 rounded-2xl font-bold text-sm">Excellent Pronunciation! +15 EXP</div>
                </div>
            </div>

            <aside class="space-y-8">
                <div class="card p-6 rounded-2xl">
                    <h4 class="font-bold mb-4 text-xs uppercase tracking-widest text-slate-400 border-b pb-2 tracking-tighter">Market Trends</h4>
                    <div class="tradingview-widget-container">
                        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js" async>
                        {{ "colorTheme": "light", "showChart": false, "locale": "ja", "isTransparent": true, "width": "100%", "height": "250",
                           "tabs": [ {{ "title": "Rates", "symbols": [ {{ "s": "FX:USDJPY" }}, {{ "s": "INDEX:N225" }}, {{ "s": "INDEX:SPX" }} ] }} ] }}
                        </script>
                    </div>
                </div>
                <div class="card p-6 rounded-2xl">
                    <h4 class="font-bold mb-4 text-xs uppercase tracking-widest text-red-600 border-b pb-2">Related Stocks</h4>
                    {stocks_html}
                </div>
                <div class="card p-6 rounded-2xl sticky top-24">
                    <h4 class="font-bold mb-6 text-xs uppercase tracking-widest text-blue-600 border-b pb-2">Vocabulary</h4>
                    <ul class="space-y-6">{"".join([f"<li><p class='text-sm font-black'>{v['w']}</p><p class='text-xs opacity-50'>{v['m']}</p></li>" for v in data['vocab']])}</ul>
                </div>
            </aside>
        </div>
    </main>

    <div class="fixed bottom-0 left-0 right-0 bg-slate-900 text-white p-4 z-50 border-t border-slate-700 backdrop-blur-md bg-opacity-90">
        <div class="max-w-4xl mx-auto flex items-center justify-between">
            <div class="flex items-center space-x-8 mx-auto">
                <button id="playBtn" onclick="togglePlay()" class="bg-white text-slate-900 w-12 h-12 rounded-full flex items-center justify-center font-bold">▶</button>
                <button onclick="resetAudio()" class="text-[10px] font-bold border border-white/20 px-3 py-1 rounded">RESET</button>
            </div>
        </div>
    </div>

    <script>
        const quizData = {quiz_json_js};
        const fullText = {full_text_js};
        const speech = new SpeechSynthesisUtterance(fullText);
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
            document.getElementById(`q${{qIdx}}-exp`).classList.remove('hidden');
            alert(optIdx === quizData[qIdx].ans ? "Correct! 🎯" : "Incorrect! ✍️");
        }}
        function toggleRec() {{
            const b = document.getElementById('recordBtn'); b.innerText = "LISTENING...";
            setTimeout(() => {{ b.innerText = "START RECORDING"; document.getElementById('feedback').classList.remove('hidden'); }}, 2500);
        }}
        speech.onend = () => {{ document.getElementById('playBtn').innerText = "▶"; isPlaying = false; }};
    </script>
</body>
</html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    
    archive_path = f"archive/{new_slug}.html"
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(full_html.replace('href="archive/', 'href="'))

    print(f"Success: {new_slug} created.")

except Exception as e:
    print(f"Error: {e}")
    exit(1)
