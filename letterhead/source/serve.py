#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Goya Ten  -  local file server for the letterhead deliverables.

Run:   python3 serve.py [port]
Then:  open http://localhost:<port>/

Routes
    /                  branded download page (Arabic / English)
    /files/<path>      a single file (?dl=1 forces "save as")
    /zip               everything in one .zip archive
"""
import io
import os
import sys
import html
import zipfile
import mimetypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote, parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../letterhead
SKIP_DIRS = {"__pycache__", "_build", ".git"}

GROUPS = [
    ("الورق الرسمي - PDF جاهز للطباعة", "Official letterhead - print ready PDF", [
        ("Goya_Ten_Letterhead_A4_Corporate.pdf", "التصميم الرئيسي (شرائط كحلي/ذهبي)",
         "Main design - navy & gold bands"),
        ("Goya_Ten_Letterhead_A4_Minimal.pdf", "تصميم بسيط أكثر",
         "Minimal alternative design"),
        ("Goya_Ten_Letterhead_Sample_Letter.pdf", "نموذج خطاب مُعبّأ بالعربية والإنجليزية",
         "Sample filled-in letter"),
    ]),
    ("قالب Word قابل للتعديل", "Editable Word template", [
        ("Goya_Ten_Letterhead_Word.docx", "الترويسة والتذييل مثبتتان في رأس/تذييل الصفحة",
         "Artwork locked into the page header & footer"),
    ]),
    ("صور ومعاينات", "Images & previews", [
        ("Goya_Ten_Letterhead_A4_Corporate.png", "الورق الرسمي - صورة 300dpi",
         "Letterhead as image"),
        ("Goya_Ten_Letterhead_A4_Minimal.png", "التصميم البسيط - صورة 300dpi",
         "Minimal design as image"),
        ("Goya_Ten_Letterhead_Margins_Guide.png", "دليل الهوامش ومنطقة الكتابة",
         "Margins / typing area guide"),
    ]),
    ("ملفات اللوجو", "Logo files", [
        ("logo/Goya_Ten_Logo_Horizontal.pdf", "لوجو أفقي - متجه (Vector)",
         "Horizontal lock-up, vector"),
        ("logo/Goya_Ten_Logo_Horizontal.png", "لوجو أفقي - خلفية بيضاء 600dpi",
         "Horizontal lock-up, white background"),
        ("logo/Goya_Ten_Logo_Horizontal_Transparent.png", "لوجو أفقي - خلفية شفافة",
         "Horizontal lock-up, transparent"),
        ("logo/Goya_Ten_Monogram.pdf", "مونوجرام GT - متجه (Vector)",
         "GT monogram, vector"),
        ("logo/Goya_Ten_Monogram.png", "مونوجرام GT - خليجي كحلي",
         "GT monogram, navy tile"),
        ("logo/Goya_Ten_Monogram_Transparent.png", "مونوجرام GT - شفاف",
         "GT monogram, transparent"),
        ("logo/Goya_Ten_Monogram_White.png", "مونوجرام أبيض - للخلفيات الداكنة",
         "White monogram - for dark backgrounds"),
    ]),
]

PREVIEWS = [
    ("Goya_Ten_Letterhead_A4_Corporate.png", "التصميم الرئيسي", "Corporate"),
    ("Goya_Ten_Letterhead_A4_Minimal.png", "التصميم البسيط", "Minimal"),
]

STYLE = """
*{box-sizing:border-box}
body{margin:0;background:#f4f6f9;color:#12233a;
     font-family:"Segoe UI",Tahoma,"Noto Sans Arabic",Arial,sans-serif;direction:rtl}
header{background:#0E2A47;color:#fff;padding:26px 22px;border-bottom:4px solid #C0A062}
header .wrap{max-width:1080px;margin:0 auto;display:flex;align-items:center;gap:18px;flex-wrap:wrap}
header img{height:64px;background:#fff;border-radius:12px;padding:4px}
h1{margin:0;font-size:24px;letter-spacing:.5px}
h1 small{display:block;font-size:13px;font-weight:400;opacity:.8;letter-spacing:1.5px;margin-top:4px}
main{max-width:1080px;margin:0 auto;padding:22px}
.bar{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;
     background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:14px 18px;margin-bottom:22px}
.bar p{margin:0;font-size:14px;color:#5b6779}
.zip{background:#C0A062;color:#12233a;text-decoration:none;font-weight:700;
     padding:12px 20px;border-radius:10px;white-space:nowrap}
.zip:hover{background:#a98a4b;color:#fff}
section{background:#fff;border:1px solid #e2e8f0;border-radius:14px;margin-bottom:20px;overflow:hidden}
section h2{margin:0;padding:14px 18px;font-size:16px;background:#f8fafc;border-bottom:1px solid #e8edf3}
section h2 span{font-weight:400;color:#7b8798;font-size:13px;margin-right:8px}
ul{list-style:none;margin:0;padding:0}
li{display:flex;align-items:center;gap:14px;padding:12px 18px;border-bottom:1px solid #f0f4f8}
li:last-child{border-bottom:0}
li:hover{background:#fafcfe}
.ext{width:46px;height:46px;flex:0 0 46px;border-radius:11px;display:flex;align-items:center;
     justify-content:center;font-size:12px;font-weight:700;color:#fff;background:#0E2A47}
.ext.pdf{background:#b3261e}.ext.docx{background:#1F5FA9}.ext.png{background:#2e7d32}
.meta{flex:1;min-width:0}
.meta b{display:block;font-size:14.5px;font-weight:600}
.meta i{display:block;font-style:normal;font-size:12.5px;color:#7b8798;margin-top:2px;
        direction:ltr;text-align:right;word-break:break-all}
.acts{display:flex;gap:8px;flex-wrap:wrap}
.acts a{text-decoration:none;font-size:13px;padding:8px 14px;border-radius:9px;
        border:1px solid #d8e0ea;color:#12233a;background:#fff}
.acts a.primary{background:#0E2A47;border-color:#0E2A47;color:#fff}
.acts a:hover{border-color:#C0A062}
.shots{display:flex;gap:16px;padding:18px;flex-wrap:wrap}
.shots figure{margin:0;flex:1 1 300px;border:1px solid #e8edf3;border-radius:12px;overflow:hidden}
.shots img{width:100%;display:block}
.shots figcaption{padding:10px 12px;font-size:13.5px;background:#f8fafc;color:#3b4a5e}
footer{max-width:1080px;margin:0 auto;padding:8px 22px 40px;color:#7b8798;font-size:12.5px;line-height:1.9}
code{background:#eef2f7;padding:2px 7px;border-radius:6px;direction:ltr;display:inline-block}
"""


def human(n):
    for unit in ("بايت", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return f"{n:,.0f} {unit}" if unit == "بايت" else f"{n/1:,.1f} {unit}"
        n /= 1024.0


def size_of(rel):
    p = os.path.join(ROOT, rel)
    return human(os.path.getsize(p)) if os.path.isfile(p) else "—"


def row(rel, ar, en):
    exists = os.path.isfile(os.path.join(ROOT, rel))
    ext = os.path.splitext(rel)[1].lstrip(".").lower()
    name = html.escape(os.path.basename(rel))
    q = "/files/" + "/".join(html.escape(part) for part in rel.split("/"))
    if not exists:
        return (f'<li><div class="ext {ext}">{ext.upper()[:4]}</div>'
                f'<div class="meta"><b>{html.escape(ar)}</b><i>{name}</i></div>'
                f'<div class="acts"><a>غير موجود</a></div></li>')
    return (
        f'<li><div class="ext {ext}">{ext.upper()[:4]}</div>'
        f'<div class="meta"><b>{html.escape(ar)}</b>'
        f'<i>{name} &nbsp;•&nbsp; {size_of(rel)}</i>'
        f'<i style="direction:rtl;text-align:right;color:#9aa5b4">{html.escape(en)}</i></div>'
        f'<div class="acts">'
        f'<a class="primary" href="{q}?dl=1">تحميل ⬇</a>'
        f'<a href="{q}" target="_blank">فتح</a>'
        f'</div></li>')


def index_html():
    shots = "".join(
        f'<figure><img src="/files/{html.escape(p)}" alt="{html.escape(ar)}" loading="lazy">'
        f'<figcaption>{html.escape(ar)} — {html.escape(en)}</figcaption></figure>'
        for p, ar, en in PREVIEWS)
    groups = ""
    for ar, en, items in GROUPS:
        rows = "".join(row(*it) for it in items)
        groups += (f'<section><h2>{html.escape(ar)}<span>{html.escape(en)}</span></h2>'
                   f'<ul>{rows}</ul></section>')
    total = 0
    for ar, en, items in GROUPS:
        for it in items:
            p = os.path.join(ROOT, it[0])
            if os.path.isfile(p):
                total += os.path.getsize(p)
    return f"""<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>جويا تن — تحميل ملفات الورق الرسمي | Goya Ten downloads</title>
<style>{STYLE}</style></head><body>
<header><div class="wrap">
  <img src="/files/logo/Goya_Ten_Monogram.png" alt="Goya Ten">
  <div><h1>جويا تن — الورق الرسمي للشركة
    <small>GOYA TEN · CORPORATE LETTERHEAD</small></h1></div>
</div></header>
<main>
  <div class="bar">
    <p>حمّل الملفات بالكامل ({human(total)}) — كل الملفات في ملف مضغوط واحد<br>
       <span style="direction:ltr;display:inline-block">Download everything in one ZIP archive</span></p>
    <a class="zip" href="/zip">⬇ تحميل الكل (ZIP) — Download all</a>
  </div>
  <section><h2>معاينة التصميم<span>Design preview</span></h2>
    <div class="shots">{shots}</div></section>
  {groups}
</main>
<footer>
  الألوان: كحلي <code>#0E2A47</code> + ذهبي <code>#C0A062</code> · الخطوط: IBM Plex Sans Arabic + Lato Black<br>
  للطباعة: اختر مقاس 100% (Actual size) بدون «Fit to page». الهاتف/الإيميل/الموقع قيم مؤقتة
  (<code>0100 000 0000</code> · <code>info@goyaten.com</code> · <code>www.goyaten.com</code>) — أرسل القيم الصحيحة لتُعدَّل.<br>
  للتحميل من جهازك مباشرة دون سيرفر: الملفات في مجلد <code>letterhead/</code> داخل المستودع.
</footer>
</body></html>"""


def safe_path(rel):
    rel = unquote(rel).lstrip("/")
    parts = [p for p in rel.split("/") if p not in ("", ".", "..")]
    if any(p in SKIP_DIRS for p in parts):
        return None
    full = os.path.join(ROOT, *parts)
    if not os.path.abspath(full).startswith(os.path.abspath(ROOT)):
        return None
    return full


def zip_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for base, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in sorted(files):
                full = os.path.join(base, f)
                z.write(full, os.path.relpath(full, ROOT))
    return buf.getvalue()


class Handler(BaseHTTPRequestHandler):
    server_version = "GoyaTenFiles/1.0"

    def log_message(self, fmt, *args):        # keep the log readable
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, body, ctype, extra=None, code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        u = urlparse(self.path)
        path, query = u.path, parse_qs(u.query)

        if path in ("/", "/index.html"):
            return self._send(index_html().encode("utf-8"), "text/html; charset=utf-8")
        if path == "/favicon.ico":
            return self._send(b"", "image/x-icon", code=204)
        if path == "/zip":
            data = zip_bytes()
            return self._send(data, "application/zip", {
                "Content-Disposition": 'attachment; filename="Goya_Ten_Letterhead.zip"'})
        if path.startswith("/files/"):
            full = safe_path(path[len("/files/"):])
            if not full or not os.path.isfile(full):
                return self._send(b"<h1>404</h1>", "text/html; charset=utf-8", code=404)
            ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
            with open(full, "rb") as fh:
                data = fh.read()
            extra = {}
            if query.get("dl"):
                name = os.path.basename(full)
                extra["Content-Disposition"] = (
                    'attachment; filename="%s"; filename*=UTF-8\'\'%s'
                    % (name.encode("ascii", "ignore").decode() or "file", name))
            else:
                extra["Content-Disposition"] = "inline"
            return self._send(data, ctype, extra)
        return self._send(b"<h1>404</h1>", "text/html; charset=utf-8", code=404)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Goya Ten file server  ->  http://localhost:{port}/   (root: {ROOT})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()
