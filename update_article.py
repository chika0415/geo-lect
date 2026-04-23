import os
import json
import datetime
import requests
import google.generativeai as genai

# --- 1. 初期設定 ---
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.5-flash')

# --- 2. 時刻とスラグの準備 ---
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
display_date = now.strftime("%Y/%m/%d %H:%M")
date_id = now.strftime("%Y%m%d")

# --- 3. 記事生成プロンプト ---
prompt = f"""
最新の地政学ニュースを1つ選び、英語学習教材を作成してください。
以下のJSON形式で厳密に出力してください：
{{
  "en_title": "英語の見出し",
  "jp_title": "日本語の見出し",
  "seo_description": "100文字程度の要約",
  "slug": "タイトルを英語の小文字とハイフンのみで表現",
  "image_query": "A cinematic, professional news photo of [記事のトピックの英語描写]",
  "segments": [{{"en": "英文", "jp": "和訳"}}],
  "advice": "投資・戦略アドバイス",
  "vocab": [{{"w": "単語", "m": "意味"}}]
}}
"""

try:
    response = model.generate_content(prompt)
    raw_json = response.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(raw_json)

    # --- 4. 画像のダウンロードと保存（場所を images/ に変更） ---
    image_dir = "images"
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs("archive", exist_ok=True)
    
    new_slug = f"{date_id}-{data['slug']}"
    image_path = f"{image_dir}/{new_slug}.jpg"
    
    # AI画像生成URL（Pollinations AIを使用）
    encoded_prompt = requests.utils.quote(data['image_query'])
    ai_image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=800&height=450&nologo=true"

    try:
        print(f"Downloading image: {ai_image_url}")
        img_res = requests.get(ai_image_url, timeout=20)
        if img_res.status_code == 200:
            with open(image_path, 'wb') as f:
                f.write(img_res.content)
            print(f"Image saved successfully: {image_path}")
        else:
            image_path = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=800" # 失敗時の宇宙写真
    except Exception as e:
        print(f"Image download error: {e}")
        image_path = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=800"

    # --- 5. データベース更新 ---
    db_file = "posts.json"
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            posts = json.load(f)
    else:
        posts = []

    new_post = {
        "date_id": date_id,
        "title": data['en_title'],
        "img": image_path, # "images/ファイル名.jpg"
        "url": f"archive/{new_slug}.html"
    }
    posts.insert(0, new_post)
    posts = posts[:20]

    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    # --- 6. HTMLパーツ作成 ---
    archive_cards_html = ""
    for p in posts[1:10]:
        date_fmt = f"{p['date_id'][:4]}/{p['date_id'][4:6]}/{p['date_id'][6:8]}"
        # カード内の画像パスを修正
        archive_cards_html += f"""
        <a href="{p['url']}" class="group block card rounded-2xl overflow-hidden hover:border-red-600 transition shadow-sm">
            <img src="{p['img']}" class="w-full h-32 object-cover group-hover:scale-105 transition duration-500">
            <div class="p-4">
                <span class="text-[10px] text-slate-400 font-bold tracking-widest">{date_fmt}</span>
                <h5 class="text-xs font-bold mt-1 group-hover:text-red-600 transition line-clamp-2 leading-tight">{p['title']}</h5>
            </div>
        </a>"""

    vocab_html = "".join([f"<li><p class='text-sm font-black'>{v['w']}</p><p class='text-xs opacity-50'>{v['m']}</p></li>" for v in data['vocab']])
    segments_html = "".join([f"""
        <div class="grid md:grid-cols-2 gap-8 border-b border-slate-200 pb-8 items-center">
            <div class="space-y-3">
                <p class="text-xl serif leading-relaxed font-medium">{s['en']}</p>
                <button onclick="playText(this)" class="text-[10px] bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded font-bold uppercase tracking-tighter">🔊 Listen</button>
            </div>
            <div class="text-lg opacity-70 italic border-l-4 border-red-600/30 pl-6 serif">{s['jp']}</div>
        </div>""" for s in data['segments']])

    # --- 7. メインHTML (index.html) ---
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
        :root {{ --bg: #f8fafc; --text: #0f172a; --card: #ffffff; --border: #e2e8f0; }}
        .dark {{ --bg: #0f172a; --text: #f1f5f9; --card: #1e293b; --border: #334155; }}
        body {{ background-color: var(--bg); color: var(--text); transition: 0.3s; font-family: 'Inter', sans-serif; }}
        .serif {{ font-family: 'Playfair Display', serif; }}
        .card {{ background-color: var(--card); border: 1px solid var(--border); }}
    </style>
</head>
<body class="antialiased">
    <header class="border-b border-slate-500/10 sticky top-0 z-50 backdrop-blur-lg bg-opacity-90">
        <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
            <h1 class="text-3xl font-black italic serif tracking-tighter">GEO-<span class="text-red-600">LECT</span></h1>
            <button onclick="document.body.classList.toggle('dark')" class="p-2 border rounded-full text-xs">MODE</button>
        </div>
    </header>
    <main class="max-w-7xl mx-auto px-6 py-12">
        <div class="max-w-4xl mb-12">
            <div class="text-red-600 font-bold mb-4 tracking-widest text-[10px] uppercase">● {display_date} Update</div>
            <h2 class="text-4xl md:text-6xl font-black mb-6 serif uppercase tracking-tighter leading-tight">{data['en_title']}</h2>
            <h3 class="text-2xl font-bold text-slate-500">{data['jp_title']}</h3>
        </div>
        <img src="{image_path}" class="w-full h-64 md:h-[450px] object-cover rounded-3xl mb-16 shadow-2xl border border-slate-200">
        <div class="grid lg:grid-cols-4 gap-12">
            <div class="lg:col-span-3 space-y-16">
                {segments_html}
                <div class="card rounded-3xl p-8 border-l-8 border-blue-600 bg-blue-600/5">
                    <h4 class="font-bold mb-3 text-blue-700 italic">🤖 Gemini's Strategy Insight</h4>
                    <p class="leading-relaxed opacity-80 text-sm">{data['advice']}</p>
                </div>
                <section class="mt-20">
                    <h4 class="font-bold mb-8 text-xs uppercase tracking-widest opacity-40 border-b pb-2">Intelligence Archive</h4>
                    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">{archive_cards_html}</div>
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
            ut.lang = 'en-US'; window.speechSynthesis.speak(ut);
        }}
    </script>
</body>
</html>
    """

    # --- 8. 保存処理 ---
    # index.htmlの保存
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    
    # アーカイブ用HTMLの作成（パスを ../ に調整）
    # archive/ 内のファイルからは画像は ../images/ になる
    archive_html = full_html.replace(f'src="{image_dir}/', f'src="../{image_dir}/')
    archive_html = archive_html.replace('href="archive/', 'href="') # アーカイブ内からは archive/ を消す
    
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

    print(f"Complete: {new_slug} created.")

except Exception as e:
    print(f"Error: {e}")
    exit(1)
