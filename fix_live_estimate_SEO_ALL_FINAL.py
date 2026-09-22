from pathlib import Path
import re
import argparse

ROOT = Path(__file__).resolve().parent

STYLE = r"""
<style id="cc-live-estimate-final">
.cc-top-actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.cc-fast-estimate{display:inline-flex!important;align-items:center;justify-content:center;background:#ffcc00!important;color:#111!important;padding:11px 18px!important;border-radius:9px!important;font-weight:900!important;text-decoration:none!important}
.cc-live-wrap{max-width:920px;margin:28px auto;padding:0 20px;text-align:left}
.cc-live-box{background:#fff;border:1px solid #dbeafe;border-radius:18px;overflow:hidden;box-shadow:0 10px 30px rgba(15,23,42,.08)}
.cc-live-title{background:#0865cf;color:#fff;padding:13px 17px;font-size:18px;font-weight:900}
.cc-live-window{height:244px;overflow:hidden;background:#fff}
.cc-live-row{height:61px;display:grid;grid-template-columns:.8fr 1.15fr 1.55fr .85fr .65fr;gap:10px;align-items:center;padding:0 16px;border-bottom:1px solid #eef2f7;font-size:14px;box-sizing:border-box}
.cc-live-date{color:#0865cf;font-weight:900}.cc-live-time{color:#64748b;text-align:right}
@media(max-width:650px){.cc-top-actions{display:grid;grid-template-columns:1fr 1fr}.cc-live-row{font-size:11px;gap:5px;padding:0 8px}}
</style>
"""

BLOCK = r"""
<!-- CHANGE_CLEAN_LIVE_ESTIMATE_FINAL -->
<section class="cc-live-wrap" aria-label="실시간 견적문의"><div class="cc-live-box">
<div class="cc-live-title">● 실시간 견적문의</div>
<div class="cc-live-window"><div id="ccLiveFinal"></div></div>
</div></section>
<script>
(function(){
const data=[["최*석","인천 송도동","입주청소 · 34평","3분 전"],["김*영","김포 장기동","이사청소 · 25평","8분 전"],["박*민","부천 중동","입주청소 · 32평","14분 전"],["이*희","고양 일산동구","거주청소 · 41평","21분 전"],["정*훈","인천 부평동","이사청소 · 28평","29분 전"],["한*진","서울 송파구","입주청소 · 24평","37분 전"]];
const t=document.getElementById("ccLiveFinal");if(!t)return;const now=new Date();
data.forEach((r,i)=>{let d=new Date(now);d.setDate(d.getDate()+2+i*3);let e=document.createElement("div");e.className="cc-live-row";e.innerHTML="<b>"+r[0]+"</b><span>"+r[1]+"</span><span>"+r[2]+"</span><span class='cc-live-date'>예약 "+(d.getMonth()+1)+"/"+d.getDate()+"</span><span class='cc-live-time'>"+r[3]+"</span>";t.appendChild(e);});
let i=0;setInterval(()=>{i=(i+1)%3;t.style.transition="transform .8s ease";t.style.transform="translateY("+(-61*i)+"px)"},3200);
})();
</script>
"""

# Exact legacy blocks found in the supplied real HTML.
LEGACY_BLOCK_RE = re.compile(
    r'<!--\s*CHANGE_CLEAN_LIVE_ESTIMATE_(?:V1|V2|FINAL\d*|FINAL)\s*-->\s*'
    r'<section class="cc-live-wrap".*?</section>\s*<script>.*?</script>',
    re.I | re.S
)
STYLE_RE = re.compile(
    r'<style\s+id=["\']cc-live-estimate-(?:style|final)["\']>.*?</style>',
    re.I | re.S
)

def clean_legacy(s):
    s = LEGACY_BLOCK_RE.sub("", s)
    s = STYLE_RE.sub("", s)
    # Remove literal \n artifacts previously injected outside tags.
    s = re.sub(r'(?m)^\s*\\n\s*$', '', s)
    return s


def plain_text(v):
    v = re.sub(r"<[^>]+>", " ", v or "")
    v = re.sub(r"\s+", " ", v).strip()
    return v

def seo_values(s):
    # Preserve each page's existing local/service wording rather than inventing one generic title.
    m = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.I | re.S)
    if m:
        base = plain_text(m.group(1))
    else:
        m = re.search(r"<title[^>]*>(.*?)</title>", s, re.I | re.S)
        base = plain_text(m.group(1)) if m else "체인지클린 청소서비스"

    # Remove common marketing tail only when it bloats the search title.
    base = re.sub(r"\s*청소업체찾기\s*$", "", base).strip()
    base = re.sub(r"\s+", " ", base).strip()

    title = base
    if "체인지클린" not in title:
        title = f"{title} | 체인지클린"
    if len(title) > 58:
        short = re.sub(r"\s*(체인지클린|청소업체찾기)\s*", " ", base).strip()
        title = (short[:45].rstrip() + " | 체인지클린") if len(short) > 45 else (short + " | 체인지클린")

    # Description is based on the page title/local keywords and avoids unsupported fixed prices.
    desc_base = re.sub(r"\s*\|\s*체인지클린\s*$", "", title).strip()
    desc = f"{desc_base} 관련 청소 범위와 비용, 작업 전 확인사항을 안내합니다. 입주청소·이사청소·거주청소 상담과 빠른 견적문의가 가능합니다."
    if len(desc) > 155:
        desc = desc[:152].rstrip(" ,·|") + "."

    return title, desc

def upsert_meta(s, title, desc):
    # title
    if re.search(r"<title[^>]*>.*?</title>", s, re.I | re.S):
        s = re.sub(r"<title[^>]*>.*?</title>", f"<title>{title}</title>", s, count=1, flags=re.I | re.S)
    else:
        s = s.replace("</head>", f"<title>{title}</title>\n</head>", 1)

    def set_meta(text, key_attr, key, content):
        pat = rf'<meta\b[^>]*\b{key_attr}\s*=\s*["\']{re.escape(key)}["\'][^>]*>'
        tag = f'<meta {key_attr}="{key}" content="{content}">'
        if re.search(pat, text, re.I):
            return re.sub(pat, tag, text, count=1, flags=re.I)
        return text.replace("</head>", tag + "\n</head>", 1)

    s = set_meta(s, "name", "description", desc)
    s = set_meta(s, "property", "og:title", title)
    s = set_meta(s, "property", "og:description", desc)
    return s

def patch_seo(s):
    title, desc = seo_values(s)
    return upsert_meta(s, title, desc)

def patch_main(s):
    s = clean_legacy(s)
    s = patch_seo(s)
    s = s.replace("</head>", STYLE + "\n</head>", 1)
    # Main pages: insert once immediately after hero section if present.
    hero = re.search(r'<section class="hero-section".*?</section>', s, re.I|re.S)
    if hero:
        pos = hero.end()
        s = s[:pos] + "\n" + BLOCK + s[pos:]
    else:
        s = s.replace("<body>", "<body>\n" + BLOCK, 1)
    return s

def patch_child(s):
    s = clean_legacy(s)
    s = patch_seo(s)
    s = s.replace("</head>", STYLE + "\n</head>", 1)
    s = s.replace("<body>", "<body>\n" + BLOCK, 1)

    # Normalize accidental nested cc-top-actions wrappers.
    s = re.sub(
        r'<div class="cc-top-actions">\s*<div class="cc-top-actions">(.*?)</div>\s*</div>',
        r'<div class="cc-top-actions">\1</div>', s, flags=re.I|re.S
    )

    # Add fast button beside direct consultation only if absent.
    if 'class="cc-fast-estimate"' not in s:
        phone = re.search(r'(<a[^>]*class=["\']phone["\'][^>]*>.*?</a>)', s, re.I|re.S)
        if phone:
            add = phone.group(1) + '<a class="cc-fast-estimate" href="#estimate">⚡ 빠른 견적문의</a>'
            s = s[:phone.start()] + add + s[phone.end():]
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--test", default="")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)

    files = [Path(args.test)] if args.test else list(root.rglob("index.html"))
    changed = 0
    main_n = child_n = 0

    for p in files:
        if not p.exists(): continue
        old = p.read_text(encoding="utf-8", errors="ignore")
        is_child = p.parent.name == "cleaning-company"
        new = patch_child(old) if is_child else patch_main(old)

        # Only touch pages that are relevant cleaning pages / already contain feature.
        relevant = ("체인지클린" in old or "CHANGE_CLEAN_LIVE_ESTIMATE" in old or "cc-live-wrap" in old)
        if not relevant: continue

        if new != old:
            bak = p.with_suffix(p.suffix + ".before_live_final.bak")
            if not bak.exists():
                bak.write_text(old, encoding="utf-8")
            p.write_text(new, encoding="utf-8")
            changed += 1
        child_n += int(is_child)
        main_n += int(not is_child)

    print(f"완료: 검사 {len(files)}개 / 수정 {changed}개")
    print(f"메인 {main_n}개 / cleaning-company {child_n}개")
    print("규칙: 실시간 견적문의 1개 유지 + 빈 중복 제거 + 빠른 견적문의 유지 + \\n 흔적 제거 + title/meta description/og:title/og:description 적용")

if __name__ == "__main__":
    main()
