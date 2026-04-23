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

# --- 3. 記事生成プロンプト (カラー生成を追加) ---
prompt = f"""
最新の地政学ニュースを1つ選び、英語学習教材を作成してください。
以下のJSON形式で厳密に出力してください（余計なテキストは含めないで）：
{{
  "en_title": "英語の見出し",
  "jp_title": "日本語の見出し",
  "slug": "タイトルを英語の小文字とハイフンのみで表現",
  "seo_description": "100文字程度の要約",
  # 【変更】 記事の内容に合う「Tailwindのグラデーションカラー」 (例: 'from-blue-600 to-indigo-900')
  "bg_gradient": "from-blue-600 to-indigo-900",
  "segments": [{{"en": "英文", "jp": "和訳"}}],
  "advice": "投資助言",
  "vocab": [{{"w": "単語", "m": "意味"}}]
}}
"""

try:
    # Geminiから記事データを取得
    response = model.generate_content(prompt)
    raw_json = response.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(raw_json)

    # --- 4. データベース更新 (posts.json) ---
    os.makedirs("archive", exist_ok=True)
    db_file = "posts.json"
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            posts = json.load(f)
    else:
        posts = []
    
    new_slug = f"{date_id}-{data['slug']}"
    
    # img パスは不要になったが、過去の互換性のために一応残す (何もしない)
    new_post = {
        "date_id": date_id,
        "title": data['en_title'],
        "url": f"archive/{new_slug}.html"
    }
    posts.insert(0, new_post)
    posts = posts[:15] # 最新15件を保存

    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    # --- 5. パーツの組み立て (カッコ修正を踏襲) ---
    archive_cards_html = ""
    for p in posts[1:10]: # 最新以外をアーカイブに
        date_display = p['date_id'][:4] + "/" + p['date_id'][4:6] + "/" + p['date_id'][6:8]
        archive_cards_html += f"""
        <a href="{p['url']}" class="group block card rounded-2xl p-6 border border-slate-700/10 hover:border-red-600 transition shadow-sm hover:shadow-lg bg-white">
            <span class="text-[10px] text-slate-400 font-bold uppercase sans">{date_display}</span>
            <h5 class="text-sm font-bold mt-1 group-hover:text-red-600 transition line-clamp-2 leading-tight serif">{p['title']}</h5>
        </a>"""

    vocab_html = "".join([f"<li><p class='text-sm font-black'>{v['w']}</p><p class='text-xs opacity-50 mt-1 sans'>{v['m']}</p></li>" for v in data['vocab']])
    
    segments_html = "".join([f"""
        <div class="grid md:grid-cols-2 gap-10 pb-10 border-b border-slate-500/10">
            <div class="space-y-4">
                <p class="text-xl serif leading-relaxed">{s['en']}</p>
                <button onclick="playText(this)" class="text-[10px] bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded font-bold uppercase tracking-tighter">🔊 Listen</button>
            </div>
            <div class="text-lg opacity-70 border-l-4 border-red-600/30 pl-6 serif">{s['jp']}</div>
        </div>""" for s in data['segments']])

    # --- 6. HTML全体の組み立て (カッコ修正を踏襲) ---
    full_html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['en_title']} | GEO-LECT Intelligence</title>
    <meta name="description" content="{data['seo_description']}">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Playfair+Display:ital,wght@0,700;1,700&display=swap" rel="stylesheet">
    <style>
        :root {{ --bg: #f8fafc; --text: #0f172a; --card: #ffffff; --border: #e2e8f0; --accent: #dc2626; }}
        .dark {{ --bg: #0f172a; --text: #f1f5f9; --card: #1e293b; --border: #334155; --accent: #f87171; }}
        body {{ background-color: var(--bg); color: var(--text); transition: all 0.3s ease; font-family: 'Inter', 'Noto Sans JP', sans-serif; }}
        .serif {{ font-family: 'Playfair Display', serif; }}
        .card {{ background-color: var(--card); border: 1px solid var(--border); }}
    </style>
</head>
<body class="antialiased">
    <header class="border-b border-slate-500/10 sticky top-0 z-50 backdrop-blur-lg bg-opacity-80">
        <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center text-slate-800 dark:text-white">
            <h1 class="text-3xl font-black italic serif tracking-tighter">GEO-<span class="text-red-600">LECT</span></h1>
            <button onclick="document.body.classList.toggle('dark')" class="p-2 border rounded-full text-xs">MODE</button>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-12">
        <div class="card rounded-3xl p-12 bg-gradient-to-br {data['bg_gradient']} mb-16 text-white shadow-2xl">
            <div class="text-white/60 font-bold mb-4 tracking-widest text-[10px] uppercase sans">● {display_date} ANALYSIS</div>
            <h2 class="text-4xl md:text-6xl font-black mb-6 serif uppercase tracking-tighter leading-tight">{data['en_title']}</h2>
            <h3 class="text-2xl font-bold text-white/80 leading-snug serif">{data['jp_title']}</h3>
        </div>

        <div class="grid lg:grid-cols-4 gap-12">
            <div class="lg:col-span-3 space-y-16">
                {segments_html}
                <div class="card rounded-3xl p-8 border-l-8 border-blue-600 bg-blue-600/5">
                    <h4 class="font-bold mb-3 text-blue-700 font-bold sans flex items-center">🤖 Gemini's Strategy insight</h4>
                    <p class="leading-relaxed opacity-80 text-sm">{data['advice']}</p>
                </div>
                <section class="mt-20">
                    <h4 class="font-bold mb-10 text-xs uppercase tracking-widest opacity-40 border-b pb-2 sans">Intelligence Archive</h4>
                    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">{archive_cards_html}</div>
                </section>
            </div>
            <aside class="space-y-8">
                <div class="card p-6 rounded-2xl sticky top-24">
                    <h4 class="font-bold mb-6 text-xs uppercase tracking-widest text-red-600 border-b pb-2 sans">Vocabulary</h4>
                    <ul class="space-y-6">{vocab_html}</ul>
                </div>
            </aside>
        </div>
    </main>
    <script>
        function playText(btn) {{
            const text = btn.previousElementSibling.innerText;
            const ut = new SpeechSynthesisUtterance(text); ut.lang = 'en-US'; window.speechSynthesis.speak(ut);
        }}
    </script>
</body>
</html>
    """

    # --- 7. 保存処理 (archiveパス調整は踏襲) ---
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    
    # アーカイブ用HTML
    archive_html = full_html.replace('href="archive/', 'href="') 
    
    with open(f"archive/{new_slug}.html", "w", encoding="utf-8") as f:
        f.write(archive_html)

    # サイトマップ更新
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += '  <url><loc>https://chika0415.github.io/geo-lect/</loc></url>\n'
    for p in posts:
        sitemap += f'  <url><loc>https://chika0415.github.io/geo-lect/{p["url"]}</loc></url>\n'
    sitemap += '</urlset>'
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap)

    print(f"Success: {new_slug} created with color gradient design.")

except Exception as e:
    print(f"Error occurred: {e}")
    exit(1)
