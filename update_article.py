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

# --- 3. 記事生成プロンプト (SEOキーワード強化) ---
prompt = f"""
最新の地政学・経済リスクから、投資家が注目すべきトピックを1つ選び、英語学習教材を作成してください。

以下のJSON形式で厳密に出力してください：
{{
  "en_title": "英語の見出し (SEOに強い具体的なもの)",
  "jp_title": "日本語の見出し",
  "seo_description": "この記事の100文字程度の要約",
  "slug": "タイトルを英語の小文字とハイフンのみで表したもの (例: vietnam-energy-crisis)",
  "image_query": "その記事に合う写真の検索用英単語1語 (例: 'refinery')",
  "segments": [{{"en": "英文", "jp": "和訳"}}],
  "advice": "投資・戦略アドバイス",
  "vocab": [{{"w": "単語", "m": "意味"}}]
}}
"""

try:
    response = model.generate_content(prompt)
    raw_json = response.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(raw_json)

    # --- 4. データベース(posts.json)の更新 ---
    os.makedirs("archive", exist_ok=True)
    db_file = "posts.json"
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            posts = json.load(f)
    else:
        posts = []

    new_slug = f"{date_id}-{data['slug']}"
    
    # 画像URLを生成（Unsplash + image_query）
    img_url = f"https://images.unsplash.com/featured/?{data['image_query']}"
    
    # 万が一 Unsplash が失敗した場合に備えて、後備（fallback）画像を用意
    fallback_img_url = "https://images.unsplash.com/photo-1590615365410-d4194f11a040?auto=format&fit=crop&q=80&w=600" # 例: Emu War写真

    new_post = {
        "date_id": date_id,
        "title": data['en_title'],
        "url": f"archive/{new_slug}.html",
        "img": img_url,
        "fallback_img": fallback_img_url
    }
    posts.insert(0, new_post)
    posts = posts[:20] # 最新20件を保持

    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    # --- 5. アーカイブUIの生成 ---
    archive_cards_html = ""
    for p in posts[1:10]: # 最新以外をアーカイブに
        date_display = p['date_id'][:4] + "/" + p['date_id'][4:6] + "/" + p['date_id'][6:8]
        # 【修正】 p['...'] はPython插值なので単一カッコ `{}` に
        archive_cards_html += f"""
        <a href="{p['url']}" class="group block card rounded-2xl overflow-hidden hover:border-red-600 transition shadow-sm">
            <img src="{p['img']}" class="w-full h-32 object-cover group-hover:scale-105 transition duration-500">
            <div class="p-4">
                <span class="text-[10px] text-slate-400 font-bold uppercase">{date_display}</span>
                <h5 class="text-xs font-bold mt-1 group-hover:text-red-600 transition line-clamp-2 leading-tight">{p['title']}</h5>
            </div>
        </a>"""

    # --- 6. HTMLテンプレート ---
    # 【修正】 v['...'] と s["..."] はPython插值なので単一カッコ `{}` に
    vocab_html = "".join([f"<li><p class='text-sm font-black'>{v['w']}</p><p class='text-xs opacity-50 mt-1'>{v['m']}</p></li>" for v in data['vocab']])
    segments_html = "".join([f"""
        <div class="grid md:grid-cols-2 gap-8 border-b border-slate-200 pb-8">
            <div class="space-y-4">
                <p class="text-xl serif leading-relaxed">{s['en']}</p>
                <button onclick="playText(this)" class="text-[10px] bg-slate-100 px-2 py-1 rounded font-bold uppercase tracking-tighter hover:bg-slate-200 transition">🔊 Listen</button>
            </div>
            <div class="text-lg opacity-60 italic border-l-4 border-red-600/30 pl-6 font-bold serif">{s['jp']}</div>
        </div>
    """ for s in data['segments']])

    # 【修正】 full_htmlテンプレート全体のカッコを見直し
    # CSSの { } は {{ }} にエスケープし、Python插值の { } は単一に。
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
        body {{ background-color: var(--bg); color: var(--text); transition: all 0.3s ease; font-family: 'Inter', sans-serif; }}
        .serif {{ font-family: 'Playfair Display', serif; }}
        .card {{ background-color: var(--card); border: 1px solid var(--border); }}
    </style>
</head>
<body class="antialiased">
    <header class="border-b border-slate-500/10 sticky top-0 z-50 backdrop-blur-lg bg-opacity-90">
        <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center text-slate-800 dark:text-white">
            <h1 class="text-3xl font-black italic serif tracking-tighter">GEO-<span class="text-red-600">LECT</span></h1>
            <button onclick="document.body.classList.toggle('dark')" class="p-2 border rounded-full text-xs">MODE</button>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-12">
        <div class="max-w-4xl mb-16">
            <div class="text-red-600 font-bold mb-4 tracking-widest text-[10px] uppercase">● {display_date} UPDATE</div>
            <h2 class="text-4xl md:text-6xl font-black mb-6 serif uppercase tracking-tighter leading-tight">{data['en_title']}</h2>
            <h3 class="text-2xl font-bold text-slate-500 leading-snug">{data['jp_title']}</h3>
        </div>

        <img src="{img_url}" onerror="this.src='{fallback_img_url}'" class="w-full h-64 md:h-96 object-cover rounded-3xl mb-16 shadow-2xl border border-slate-200">

        <div class="grid lg:grid-cols-4 gap-12">
            <div class="lg:col-span-3 space-y-16">
                {segments_html}
                <div class="card rounded-3xl p-8 border-l-8 border-blue-600 bg-blue-600/5">
                    <h4 class="font-bold mb-3 text-blue-700 italic">🤖 Gemini's Strategy Insight</h4>
                    <p class="leading-relaxed opacity-80 text-sm">{data['advice']}</p>
                </div>
                
                <section class="mt-20">
                    <h4 class="font-bold mb-8 text-xs uppercase tracking-widest opacity-40 border-b pb-2">Intelligence Archive</h4>
                    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
                        {archive_cards_html}
                    </div>
                </section>
            </div>

            <aside class="space-y-8">
                <div class="card p-6 rounded-2xl sticky top-24">
                    <h4 class="font-bold mb-6 text-xs uppercase tracking-widest text-red-600 border-b pb-2">Vocabulary</h4>
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
    </script>
</body>
</html>
    """

    # --- 7. ファイル保存 ---
    with open("index.html", "w", encoding="utf-8") as f: f.write(full_html)
    with open(f"archive/{new_slug}.html", "w", encoding="utf-8") as f: f.write(full_html)

    # サイトマップ自動更新
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += '  <url><loc>https://chika0415.github.io/geo-lect/</loc></url>\n'
    for p in posts:
        # 【修正】 p["..."] はPython插值なので単一カッコ `{}` に
        sitemap += f'  <url><loc>https://chika0415.github.io/geo-lect/{p["url"]}</loc></url>\n'
    sitemap += '</urlset>'
    with open("sitemap.xml", "w", encoding="utf-8") as f: f.write(sitemap)

    print(f"Success: {new_slug} created with dynamic image and corrected HTML.")

except Exception as e:
    print(f"Error occurred: {e}")
    exit(1)
