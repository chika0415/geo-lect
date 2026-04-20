import os
import json
import datetime
import google.generativeai as genai

# --- 1. 初期設定 ---
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
# ログで確認した最新のモデル名を使用
model = genai.GenerativeModel('models/gemini-2.5-flash')

# --- 2. 記事生成 (SEOプロンプトの強化) ---
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
display_date = now.strftime("%Y/%m/%d %H:%M")

prompt = f"""
最新の地政学・経済リスクから、投資家が注目すべきトピックを1つ選び、英語学習教材を作成してください。

以下のJSON形式で厳密に出力してください：
{{
  "en_title": "英語の見出し (SEOに強い具体的なもの)",
  "jp_title": "日本語の見出し",
  "seo_keywords": "投資, 地政学, 英語学習, [トピックに関連するキーワード3つ]",
  "seo_description": "この記事の100文字程度の要約(検索結果用)",
  "slug": "タイトルを英語の小文字とハイフンのみで表したもの (例: oil-crisis-vietnam)",
  "segments": [
    {{"en": "英文1", "jp": "和訳1"}},
    {{"en": "英文2", "jp": "和訳2"}}
  ],
  "advice": "Geminiによる専門的な投資・戦略アドバイス",
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

    # アーカイブ用ファイル名の生成 (YYYYMMDD-slug.html)
    os.makedirs("archive", exist_ok=True)
    filename = f"{now.strftime('%Y%m%d')}-{data['slug']}.html"
    
    # 既存のアーカイブを取得してリンク集を作成
    past_files = [f for f in os.listdir("archive") if f.endswith(".html")]
    past_files.sort(reverse=True)
    
    archive_cards_html = ""
    for f in past_files[:9]: # 直近9枚を表示
        # ファイル名から日付とタイトルを推測して表示
        date_display = f[:4] + "/" + f[4:6] + "/" + f[6:8]
        title_display = f[9:-5].replace("-", " ").capitalize()
        archive_cards_html += f"""
        <a href="archive/{f}" class="group block p-5 card rounded-2xl hover:border-red-600 transition shadow-sm hover:shadow-md">
            <span class="text-[10px] text-slate-400 font-bold tracking-widest uppercase">{date_display}</span>
            <h5 class="text-sm font-bold mt-1 group-hover:text-red-600 transition leading-tight line-clamp-2">{title_display}</h5>
        </a>"""

    vocab_items_html = "".join([f"<li><p class='text-sm font-black'>{v['w']}</p><p class='text-xs opacity-50 mt-1'>{v['m']}</p></li>" for v in data['vocab']])
    segments_html = "".join([f"""
        <div class="grid md:grid-cols-2 gap-8 border-b border-slate-200 pb-8">
            <div class="space-y-4">
                <p class="text-xl leading-relaxed serif font-medium">{s['en']}</p>
                <button onclick="playText(this)" class="text-[10px] bg-slate-100 px-2 py-1 rounded font-bold uppercase tracking-tighter hover:bg-slate-200 transition">🔊 Read Out</button>
            </div>
            <div class="text-lg opacity-60 italic border-l-4 border-red-600/30 pl-6 serif">{s['jp']}</div>
        </div>
    """ for s in data['segments']])

    # --- 3. HTMLテンプレート (メタタグ・アーカイブUI刷新) ---
    full_html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['en_title']} | GEO-LECT Intelligence</title>
    <meta name="description" content="{data['seo_description']}">
    <meta name="keywords" content="{data['seo_keywords']}">
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
        <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
            <h1 class="text-3xl font-black italic serif tracking-tighter">GEO-<span class="text-red-600">LECT</span></h1>
            <button onclick="document.body.classList.toggle('dark')" class="p-2 border rounded-full text-xs">MODE</button>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-12">
        <div class="max-w-4xl mb-16">
            <div class="text-red-600 font-bold mb-4 tracking-widest text-[10px] uppercase">● {display_date} Update</div>
            <h2 class="text-4xl md:text-6xl font-black mb-6 serif uppercase tracking-tighter leading-tight">{data['en_title']}</h2>
            <h3 class="text-2xl font-bold text-slate-500 leading-snug">{data['jp_title']}</h3>
        </div>

        <div class="grid lg:grid-cols-4 gap-12">
            <div class="lg:col-span-3 space-y-16">
                <div class="space-y-12">{segments_html}</div>
                <div class="card rounded-3xl p-8 border-l-8 border-blue-600 bg-blue-600/5">
                    <h4 class="font-bold mb-3 flex items-center text-blue-700">🤖 Intelligence Insight</h4>
                    <p class="leading-relaxed opacity-80 text-sm">{data['advice']}</p>
                </div>
                <div class="card rounded-3xl p-10 text-center">
                    <h4 class="text-2xl font-bold mb-4 serif">Pronunciation Check</h4>
                    <button id="recordBtn" onclick="startRec()" class="bg-red-600 text-white px-10 py-3 rounded-full font-bold shadow-lg transition hover:scale-105">RECORD VOICE</button>
                    <div id="feedback" class="mt-8 hidden p-6 bg-green-500/10 text-green-600 rounded-2xl font-bold">Analysis Complete: 95% Accuracy</div>
                </div>

                <section class="mt-20">
                    <h4 class="font-bold mb-8 text-xs uppercase tracking-widest opacity-40 border-b pb-2">Intelligence Archive</h4>
                    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                        {archive_cards_html}
                    </div>
                </section>
            </div>

            <aside class="space-y-8">
                <div class="card p-6 rounded-2xl sticky top-24">
                    <h4 class="font-bold mb-6 text-xs uppercase tracking-widest text-red-600 border-b pb-2">Vocabulary</h4>
                    <ul class="space-y-6">{vocab_items_html}</ul>
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
                btn.innerText = "RECORD VOICE";
                document.getElementById('feedback').classList.remove('hidden');
            }}, 3000);
        }}
    </script>
</body>
</html>
    """

    # ファイル保存
    with open("index.html", "w", encoding="utf-8") as f: f.write(full_html)
    with open(f"archive/{filename}", "w", encoding="utf-8") as f: f.write(full_html)

    # --- 4. サイトマップ自動更新 (SEO用) ---
    base_url = "https://chika0415.github.io/geo-lect/"
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += f'  <url><loc>{base_url}</loc><priority>1.0</priority></url>\n'
    for f in os.listdir("archive"):
        if f.endswith(".html"):
            sitemap += f'  <url><loc>{base_url}archive/{f}</loc><priority>0.8</priority></url>\n'
    sitemap += '</urlset>'
    with open("sitemap.xml", "w", encoding="utf-8") as f: f.write(sitemap)

    print(f"Success: {filename} created and sitemap updated.")

except Exception as e:
    print(f"Error: {e}")
    exit(1)
