import os
import json
import datetime
import requests # 【追加】 画像ダウンロード用
import google.generativeai as genai

# --- 1. 初期設定 ---
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
# ログで確認した最新のモデル名を使用
model = genai.GenerativeModel('models/gemini-2.5-flash')

# --- 2. 時刻の準備 ---
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
display_date = now.strftime("%Y/%m/%d %H:%M")
date_id = now.strftime("%Y%m%d")

# --- 3. 記事生成プロンプト (Imagenプロンプト生成を追加) ---
prompt = f"""
最新の地政学ニュースを1つ選び、英語学習教材を作成してください。
以下のJSON形式で厳密に出力してください（余計なテキストは含めないで）：
{{
  "en_title": "英語の見出し",
  "jp_title": "日本語の見出し",
  "seo_description": "100文字程度の要約",
  "slug": "タイトルを英語の小文字とハイフンのみで表現",
  # 【追加】 AI画像生成用プロンプト (例: 'A photorealistic, cinematic image of...')
  "imagen_prompt": "A photorealistic, cinematic image related to the topic. [詳細な描写]",
  "segments": [{{"en": "英文", "jp": "和訳"}}],
  "advice": "投資・戦略アドバイス",
  "vocab": [{{"w": "単語", "m": "意味"}}]
}}
"""

try:
    # Geminiから記事を取得
    response = model.generate_content(prompt)
    raw_json = response.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(raw_json)

    # --- 4. 画像の生成と保存 (根本解決) ---
    # 画像フォルダの準備
    os.makedirs("archive/images", exist_ok=True)
    new_slug = f"{date_id}-{data['slug']}"
    # リポジトリ内での保存パス
    image_filename = f"archive/images/{new_slug}.jpg"
    
    # 【追加】 AI画像生成 (仮定のコード、sdkの仕様に合わせる)
    # 今回は requests で静的なURLからダウンロードする形にする。
    # レート制限を回避するため、静的なURLをプレースホルダーとしてダウンロードする。
    
    # AI生成画像っぽいプレースホルダー画像 (例: pollination.ai を使用)
    placeholder_base_url = "https://pollinations.ai/p/"
    encoded_prompt = requests.utils.quote(data['imagen_prompt'])
    ai_placeholder_url = f"{placeholder_base_url}{encoded_prompt}?width=800&height=450&nologo=true&enhance=false"
    
    # 画像のダウンロード
    print(f"Downloading image from: {ai_placeholder_url}")
    # 保険：もしダウンロードに失敗したら fallback画像にする
    fallback_static_img_url = "https://images.unsplash.com/photo-1590615365410-d4194f11a040?q=80&w=800"
    
    try:
        img_data = requests.get(ai_placeholder_url, timeout=15).content
        with open(image_filename, 'wb') as f:
            f.write(img_data)
        image_src_path = f"images/{new_slug}.jpg" # HTML内でのローカルパス
        print(f"Image saved to: {image_filename}")
    except Exception as img_e:
        print(f"Failed to download image: {img_e}. Using fallback URL.")
        image_src_path = fallback_static_img_url # 外部URLのままにする

    # --- 5. データベース(posts.json)の更新 (パスをローカルに) ---
    db_file = "posts.json"
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            posts = json.load(f)
    else:
        posts = []
    
    # posts.json 内の img パスを修正 (index.html から見たローカルパス)
    new_post = {
        "date_id": date_id,
        "title": data['en_title'],
        "img": image_src_path,
        "url": f"archive/{new_slug}.html"
    }
    posts.insert(0, new_post)
    posts = posts[:15] # 最新15件を保存

    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    # --- 5. パーツの組み立て (カッコ修正は前回のまま踏襲) ---
    archive_cards_html = ""
    for p in posts[1:10]: # 最新以外をアーカイブに
        date_display = p['date_id'][:4] + "/" + p['date_id'][4:6] + "/" + p['date_id'][6:8]
        # p['img'] は index.html から見たローカルパス (images/...)
        archive_cards_html += f"""
        <a href="{p['url']}" class="group block card rounded-2xl overflow-hidden hover:border-red-600 transition shadow-sm">
            <img src="{p['img']}" class="w-full h-32 object-cover group-hover:scale-105 transition duration-500">
            <div class="p-4">
                <span class="text-[10px] text-slate-400 font-bold uppercase">{date_display}</span>
                <h5 class="text-xs font-bold mt-1 group-hover:text-red-600 transition line-clamp-2 leading-tight">{p['title']}</h5>
            </div>
        </a>"""

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

    # --- 6. HTML全体の組み立て (カッコ修正は前回のまま踏襲) ---
    # CSSの { } は {{ }} にエスケープし、Python插値の { } は単一に。
    # メイン画像srcをローカルパスに変更
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

        <img src="{image_src_path}" class="w-full h-64 md:h-96 object-cover rounded-3xl mb-16 shadow-2xl border border-slate-200">

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
    # 最新版を root に保存
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    
    # 【変更】 アーカイブ用HTMLを保存する際に、パスを相対パスに置換
    # rootからのローカルパス (images/...) を、archive/ フォルダから見たローカルパス (../images/...) に置換
    archive_html = full_html.replace(f'src="{image_src_path}"', f'src="../{image_src_path}"')
    
    # 過去記事カードの src="images/..." を src="../images/..." に置換
    archive_html = archive_html.replace('src="images/', 'src="../images/')
    
    # 過去記事カードの href="archive/..." を href="..." に置換
    # (自分自身へのリンクも相対パスになる)
    archive_html = archive_html.replace('href="archive/', 'href="')
    
    with open(f"archive/{new_slug}.html", "w", encoding="utf-8") as f:
        f.write(archive_html)

    # サイトマップ作成 (前回のカッコ修正のまま)
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += '  <url><loc>https://chika0415.github.io/geo-lect/</loc></url>\n'
    for p in posts:
        sitemap += f'  <url><loc>https://chika0415.github.io/geo-lect/{p["url"]}</loc></url>\n'
    sitemap += '</urlset>'
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap)

    print(f"Success: {new_slug} created with local image saved.")

except Exception as e:
    print(f"Error occurred: {e}")
    exit(1)
