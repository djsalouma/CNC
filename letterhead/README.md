# جويا تن — الورق الرسمي للشركة | Goya Ten — Corporate Letterhead

ترويسة رسمية بجودة طباعة عالية (A4) بالعربية والإنجليزية، مع اللوجو، بتصميم واحد
يُنتَج منه ملف PDF جاهز للطباعة + قالب Word قابل للتعديل + ملفات اللوجو.

A print-ready A4 corporate letterhead in Arabic + English, produced from a single
design source: vector PDF, an editable Word template, and the logo files.

---

## 1) الملفات الجاهزة للاستخدام (Ready-to-use files)

| الملف | الوصف |
|---|---|
| `Goya_Ten_Letterhead_A4_Corporate.pdf` | الورق الرسمي — التصميم الرئيسي (شرائط كحلي/ذهبي) — **A4، 2 صفحات بالضبط، جاهز للطباعة** |
| `Goya_Ten_Letterhead_A4_Minimal.pdf` | نفس الورق بتصميم بسيط أكثر (خطوط رفيعة، بدون شرائط) |
| `Goya_Ten_Letterhead_Word.docx` | **قالب Word قابل للتعديل** — الترويسة والتذييل مثبتان تلقائيًا في رأس/تذييل الصفحة، والنص يُكتب في المنتصف |
| `Goya_Ten_Letterhead_Sample_Letter.pdf` | نموذج خطاب مُعبّأ يوضح شكل الورق مع النص (عربي + إنجليزي) |
| `Goya_Ten_Letterhead_Margins_Guide.png` | دليل الهوامش — يوضح منطقة الكتابة (50 مم إلى 262 مم) |
| `Goya_Ten_Letterhead_A4_*.png` | نسخة صورة (300 dpi) من الورق لاستخدامها في الإيميل أو العروض |
| `logo/` | ملفات اللوجو بكل الصيغ |

### ملفات اللوجو (logo/)

| الملف | الاستخدام |
|---|---|
| `Goya_Ten_Logo_Horizontal.pdf` / `.png` | اللوجو الأفقي (المونوجرام + الاسم) — خلفية بيضاء |
| `Goya_Ten_Logo_Horizontal_Transparent.png` | نفس اللوجو بخلفية شفافة |
| `Goya_Ten_Monogram.pdf` / `.png` / `..._Transparent.png` | المونوجرام المربع (GT) بخلفية كحلية |
| `Goya_Ten_Monogram_White.pdf` / `.png` | المونوجرام بالأبيض — للخلفيات الداكنة أو الصور |

> ملفات الـ PDF موجّهة (Vector) — تكبر لأي حجم بدون فقدان جودة. ملفات PNG بدقة 600 dpi.

---

## 2) بيانات الشركة المستخدمة (Content)

* **الاسم بالعربية:** جويا تن · **بالإنجليزية:** GOYA TEN
* **العنوان:** شارع 105، المعادي، القاهرة، مصر
  · 105 Street, Maadi, Cairo, Egypt
* **الهاتف / الإيميل / الموقع** — قيم مؤقتة (Placeholder) يجب تعديلها:

| | القيمة المؤقتة |
|---|---|
| هاتف / Tel | `0100 000 0000` |
| بريد / Email | `info@goyaten.com` |
| موقع / Web | `www.goyaten.com` |

للتعديل: افتح `source/stationery.py` وغيّر قيم `TEL` و `MAIL` و `WEB` (أعلى الملف)،
ثم أعد التشغيل — أو عدّلها مباشرة من داخل Word.

---

## 3) الهوية البصرية (Brand identity)

| العنصر | القيمة |
|---|---|
| الكحلي (أساسي) | `#0E2A47` |
| الكحلي الفاتح | `#1B4066` |
| الذهبي (تمييز) | `#C0A062` |
| الرمادي (نصوص ثانوية) | `#6E7681` |
| رمادي الخطوط | `#D9DEE5` |
| خط العناوين العربية | IBM Plex Sans Arabic (Bold/Medium/Regular) |
| خط النصوص اللاتينية | Carlito / Calibri |
| خط الاسم GOYA TEN | Lato Black مع تباعد حروف |

مقاس الورق A4 (210 × 297 مم) · مقاس الخطاب: ترويسة 46 مم من الأعلى، تذييل 30.5 مم من
الأسفل، ومنطقة الكتابة من 50 مم إلى 262 مم، وهوامش جانبية 20 مم.

* English name lock-up: `GOYA TEN` in Lato Black, letter-spaced.
* Arabic name: `جويا تن` (IBM Plex Sans Arabic Bold).
* Palette, sizes and margins above are the exact values used by the generator.

---

## 4) مصادر التصميم (Source / how to regenerate)

```
source/
├── design.py         # ألوان وهوية ومقاسات + مسارات الخطوط
├── typeset.py        # تشكيل عربي (HarfBuzz) + ترتيب بصري (python-bidi) + رسم Glyphs
├── stationery.py     # دوال رسم الترويسة والتذييل واللوجو  ← عدّل الأرقام من هنا
├── render_assets.py  # ينتج: PDF، PNG، شرائح Word، ملفات اللوجو
├── make_docx.py      # ينتج قالب Word
├── requirements.txt  # المكتبات المطلوبة
└── fonts/            # الخطوط المستخدمة (مرفقة)
```

إعادة التوليد كاملةً:

```bash
pip install -r source/requirements.txt
python source/render_assets.py     # PDF + PNG + logo + شرائح Word
python source/make_docx.py         # ملف Word
```

> ملاحظة: النص العربي في PDF مرسوم كمسارات متجهة (Outlines) لضمان ثبات الشكل عند أي
> مستخدم، مع طبقة نص غير مرئية تجعل الملف قابلًا للبحث والنسخ.

---

## 5) الطباعة (Printing notes)

* اطبع بمقاس 100% (Actual size) — بدون "Fit to page".
* الورق الرسمي مصمم بحواف ممتدة (Full bleed) في الشريط الكحلي العلوي والتذييل السفلي.
  للطباعة في مطبعة، اطلب إضافة 3 مم Bleed وقصّ.
* الألوان: الكحلي `#0E2A47` والذهبي `#C0A062` (للمطبعة: أعطهم هذه القيم؛ لأقرب
  مطابقة CMYK اطلب معايرة اللون قبل الطباعة الكبيرة).

---

## 6) غير موجود في هذا الإصدار (Not included yet)

* رقم الهاتف والبريد والموقع الحقيقي (قيم مؤقتة الآن).
* السجل التجاري / البطاقة الضريبية / رقم ضريبي في التذييل.
* نسخة A5 أو ظرف بريدي (Envelope) أو بطاقة أعمال — يمكن إضافتها بنفس التصميم.

> **ملاحظة مهمة:** لم يصل إلينا ملف اللوجو المرفق (المرفقات لم تُنقل إلى بيئة العمل)،
> لذلك صُمّم شعار مؤقت على شكل مونوجرام «GT» بألوان الشركة كي يكتمل الورق. عند إرسال
> ملف اللوجو الأصلي سيتم استبداله في كل الملفات فورًا.

> **Important:** the attached logo file did not reach this workspace, so a temporary
> "GT" monogram in the company colours was designed to complete the letterhead.
> Send the original logo file (PNG/SVG/PDF/AI) and it will be dropped into every
> file instead — no other change required.
