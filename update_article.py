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

# --- 3. 生成プロンプト ---
prompt = f"""
最新の「世界政治」または「国際経済」のニュースを1つ選び、学習コンテンツを作成してください。
以下のJSON形式のみを出力してください（余計なテキストは不要）：
{{
  "en_title": "英語見出し",
  "jp_title": "日本語見出し",
  "slug": "英語スラグ (例: tech-war-us-china)",
  "seo_description": "要約",
  "toeic_level": "推奨スコア (例: 850+)",
  "bg_gradient": "Tailwindグラデーション (例: from-blue-900 to-black)",
  "full_text_en": "読み上げ用全文",
  "segments": [{{ "en": "英文", "jp": "和訳" }}],
  "stocks": [{{ "name": "企業名", "code": "コード4桁" }}],
  "quiz": [{{ "q": "問題", "options": ["A", "B", "C"], "ans": 0, "exp": "解説" }}],
  "advice": "専門的アドバイス",
  "vocab": [{{ "w": "単語", "m": "意味" }}]
}}
"""

try:
    response = model.generate_content(prompt)
    raw_json = response.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(raw_json)

    # 4. データベース更新 (posts.json)
    db_file = "posts.json"
    posts = json.load(open(db_file, "r", encoding="utf-8")) if os.path.exists(db_file) else []
    new_slug = f"{date_id}-{data['slug']}"
    
    # 既存のリストに同じスラッグがあればスキップ、なければ追加
    if not any(p.get('slug') == new_slug for p in posts):
        posts.insert(0, {
            "date_id": date_id, 
            "title": data['en_title'], 
            "slug": new_slug,
            "url": f"archive/{new_slug}.html"
        })
    # posts.jsonには無制限に蓄積（archive.html用）
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    # 5. パーツ組み立て (最新4件のカード)
    def gen_cards(items, is_root=True):
        prefix = "" if is_root else "../"
        html = ""
        for p in items:
            date_fmt = f"{p['date_id'][:4]}/{p['date_id'][4:6]}/{p['date_id'][6:8]}"
            url = p['url'] if is_root else p['url'].replace("archive/", "")
            html += f"""
            <a href="{prefix}{url}" class="group block card rounded-2xl p-5 border border-slate-700/10 hover:border-red-600 transition bg-white shadow-sm">
                <span class="text-[10px] text-slate-400 font-bold uppercase sans">{date_fmt}</span>
                <h5 class="text-sm font-bold mt-1 group-hover:text-red-600 transition line-clamp-2 leading-tight serif">{p['title']}</h5>
            </a>"""
        return html

    stocks_html = "".join([f'<a href="https://jp.tradingview.com/symbols/TSE-{s["code"]}/" target="_blank" class="block p-3 border rounded-xl hover:bg-slate-50 mb-2 shadow-sm"><p class="text-[10px] font-bold text-blue-600">TSE: {s["code"]}</p><p class="text-xs font-black">{s["name"]}</p></a>' for s in data['stocks']])
    vocab_html = "".join([f"<li><p class='text-sm font-black'>{v['w']}</p><p class='text-xs opacity-50'>{v['m']}</p></li>" for v in data['vocab']])
    segments_html = "".join([f'<div class="grid md:grid-cols-2 gap-8 pb-8 border-b mb-8"><div class="text-xl serif leading-relaxed">{s["en"]}</div><div class="text-lg opacity-70 italic border-l-4 border-red-600/30 pl-6 serif font-bold">{s["jp"]}</div></div>' for s in data['segments']])
    
    quiz_html = ""
    for i, q in enumerate(data['quiz']):
        opts = "".join([f'<button onclick="checkQuiz({i}, {j})" class="block w-full text-left p-3 border rounded-lg text-sm hover:bg-white transition">{opt}</button>' for j, opt in enumerate(q['options'])])
        quiz_html += f'<div class="mb-6 p-6 bg-slate-50 dark:bg-slate-800/50 rounded-2xl"><p class="font-bold mb-4">Q{i+1}. {q["q"]}</p><div class="space-y-2">{opts}</div><p id="q{i}-exp" class="hidden text-xs text-slate-500 mt-4 pt-4 border-t italic">{q["exp"]}</p></div>'

    # 6. HTMLテンプレート生成
    def get_template(is_root=True):
        prefix = "" if is_root else "../"
        archive_link = "archive.html" if is_root else "../archive.html"
        home_link = "index.html" if is_root else "../index.html"
        
        return f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{data['en_title']}} | GEO-LECT</title>
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
        <a href="{home_link}"><h1 class="text-3xl font-black italic serif">GEO-<span class="text-red-600">LECT</span></h1></a>
        <div class="flex items-center space-x-4">
            <span class="bg-blue-100 text-blue-700 text-[10px] font-black px-3 py-1 rounded-full border border-blue-200">TOEIC {{data['toeic_level']}}</span>
            <button onclick="document.body.classList.toggle('dark')" class="p-2 border rounded-full text-xs font-bold uppercase">Mode</button>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-12">
        <div class="card rounded-3xl p-12 bg-gradient-to-br {{data['bg_gradient']}} mb-16 text-white shadow-2xl">
            <div class="text-white/60 font-bold mb-4 tracking-widest text-[10px] uppercase">● {{display_date}} ANALYSIS</div>
            <h2 class="text-4xl md:text-6xl font-black mb-6 serif uppercase tracking-tighter leading-tight">{{data['en_title']}}</h2>
            <h3 class="text-2xl font-bold text-white/80 leading-snug serif">{{data['jp_title']}}</h3>
        </div>

        <div class="grid lg:grid-cols-4 gap-12">
            <div class="lg:col-span-3 space-y-16">
                <div>{{segments_html}}</div>
                <div class="card rounded-3xl p-8 border-l-8 border-blue-600 bg-blue-600/5">
                    <h4 class="font-bold mb-3 text-blue-700 italic flex items-center sans">🤖 STRATEGIC INSIGHT</h4>
                    <p class="leading-relaxed opacity-80 text-sm font-bold">{{data['advice']}}</p>
                </div>
                <section class="card rounded-3xl p-10 shadow-xl">
                    <h4 class="text-2xl font-bold mb-8 serif uppercase border-b pb-4">Understanding Check</h4>
                    {{quiz_html}}
                </section>
                
                <section class="mt-20">
                    <div class="flex justify-between items-center mb-8 border-b pb-2">
                        <h4 class="font-bold text-xs uppercase tracking-widest opacity-40 sans">Latest Intelligence</h4>
                        <a href="{archive_link}" class="text-[10px] font-bold text-red-600 hover:underline">VIEW ALL ARCHIVES →</a>
                    </div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                        {{latest_4_cards}}
                    </div>
                </section>
            </div>

            <aside class="space-y-8">
                <div class="card p-6 rounded-2xl shadow-sm">
                    <h4 class="font-bold mb-4 text-[10px] uppercase tracking-widest text-slate-400 border-b pb-2">All Access</h4>
                    <a href="{archive_link}" class="block w-full text-center py-3 bg-slate-900 text-white rounded-xl text-xs font-bold hover:bg-red-600 transition">DATABASE ARCHIVE</a>
                </div>
                <div class="card p-6 rounded-2xl">
                    <h4 class="font-bold mb-4 text-[10px] uppercase tracking-widest text-slate-400 border-b pb-2 tracking-tighter">Market Trends</h4>
                    <div class="tradingview-widget-container">
                        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js" async>
                        {{ "colorTheme": "light", "showChart": false, "locale": "ja", "isTransparent": true, "width": "100%", "height": "250",
                           "tabs": [ {{ "title": "Rates", "symbols": [ {{ "s": "FX:USDJPY" }}, {{ "s": "INDEX:N225" }}, {{ "s": "INDEX:SPX" }} ] }} ] }}
                        </script>
                    </div>
                </div>
                <div class="card p-6 rounded-2xl">
                    <h4 class="font-bold mb-4 text-[10px] uppercase tracking-widest text-red-600 border-b pb-2 sans">Related Stocks</h4>
                    {{stocks_html}}
                </div>
                <div class="card p-6 rounded-2xl sticky top-24">
                    <h4 class="font-bold mb-6 text-[10px] uppercase tracking-widest text-blue-600 border-b pb-2">Vocabulary</h4>
                    <ul class="space-y-6">{{vocab_html}}</ul>
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
        const quizData = {json.dumps(data['quiz'], ensure_ascii=False)};
        const speech = new SpeechSynthesisUtterance({json.dumps(data['full_text_en'], ensure_ascii=False)});
        speech.lang = 'en-US'; speech.rate = 0.9;
        let isPlaying = false;
        function togglePlay() {{
            const btn = document.getElementById('playBtn');
            if (!isPlaying) {{
                if (window.speechSynthesis.paused) window.speechSynthesis.resume();
                else window.speechSynthesis.speak(speech);
                btn.innerText = "II"; isPlaying = true;
            }} else {{ window.speechSynthesis.pause(); btn.innerText = "▶"; isPlaying = false; }}
        }}
        function resetAudio() {{ window.speechSynthesis.cancel(); isPlaying = false; document.getElementById('playBtn').innerText = "▶"; }}
        function checkQuiz(qIdx, optIdx) {{
            document.getElementById(`q${{qIdx}}-exp`).classList.remove('hidden');
            alert(optIdx === quizData[qIdx].ans ? "Correct! 🎯" : "Incorrect! ✍️");
        }}
        speech.onend = () => {{ document.getElementById('playBtn').innerText = "▶"; isPlaying = false; }};
    </script>
</body>
</html>
"""

    # --- 7. 保存処理 ---
    latest_4_cards = gen_cards(posts[1:5], is_root=True)
    
    # index.html (最新記事ページ)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(get_template(is_root=True).replace("{{segments_html}}", segments_html).replace("{{latest_4_cards}}", latest_4_cards).replace("{{stocks_html}}", stocks_html).replace("{{vocab_html}}", vocab_html).replace("{{quiz_html}}", quiz_html))

    # archive.html (全一覧ページ)
    all_cards = gen_cards(posts, is_root=True) # archive.htmlもrootにあるのでTrue
    archive_body = f"""
    <div class="max-w-7xl mx-auto px-6 py-12">
        <h2 class="text-4xl font-black serif mb-12 border-b-4 border-red-600 inline-block">INTELLIGENCE DATABASE</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">{all_cards}</div>
    </div>"""
    # 簡易的な一覧用テンプレート（indexの構造を流用）
    with open("archive.html", "w", encoding="utf-8") as f:
        # 一覧ページなので、メイン記事部分を archive_body に差し替え
        f.write(get_template(is_root=True).replace("{{segments_html}}", archive_body).replace("{{latest_4_cards}}", "").replace("{{stocks_html}}", "").replace("{{vocab_html}}", "").replace("{{quiz_html}}", ""))

    # 各アーカイブ詳細ページ
    for p in posts:
        # すでにファイルがある場合はスキップしても良いが、デザイン更新のために毎回上書き
        # (※ただし、data変数が現在の生成分なので、過去の内容を保持するにはDBに全文保存が必要)
        # 今回は、生成された瞬間の記事のみを archive/ に保存する
        pass
    
    # 現在の記事を archive/ に保存
    latest_4_cards_relative = gen_cards(posts[1:5], is_root=False)
    with open(f"archive/{new_slug}.html", "w", encoding="utf-8") as f:
        f.write(get_template(is_root=False).replace("{{segments_html}}", segments_html).replace("{{latest_4_cards}}", latest_4_cards_relative).replace("{{stocks_html}}", stocks_html).replace("{{vocab_html}}", vocab_html).replace("{{quiz_html}}", quiz_html))

    print(f"Update Success: index.html and archive.html updated. New article: {new_slug}")

except Exception as e:
    print(f"Error: {e}")
    exit(1)
