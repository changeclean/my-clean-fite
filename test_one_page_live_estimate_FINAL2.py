# -*- coding: utf-8 -*-
import argparse, re
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--file",required=True)
a=ap.parse_args()
p=Path(a.file).resolve()
if not p.exists(): raise SystemExit("파일 없음: "+str(p))

s=p.read_text(encoding="utf-8",errors="ignore")
bak=p.with_name(p.name+".before_fix_test2.bak")
if not bak.exists(): bak.write_text(s,encoding="utf-8")

# 1) 기존 실시간 견적문의 섹션을 모두 제거.
# cc-live-wrap 시작점을 찾고, 그 뒤 script 종료까지 반복 제거.
while True:
    m=re.search(r'<section[^>]*cc-live-wrap[^>]*>',s,re.I)
    if not m: break
    sec_end=s.find("</section>",m.end())
    if sec_end<0: break
    end=sec_end+10
    sm=re.match(r'\\s*<script[^>]*>.*?</script>',s[end:],re.I|re.S)
    if sm: end+=sm.end()
    # 앞의 마커 주석도 제거
    start=m.start()
    prefix=s[max(0,start-120):start]
    cm=re.search(r'<!--\\s*CHANGE_CLEAN_LIVE_ESTIMATE[^>]*-->\\s*$',prefix,re.I)
    if cm: start=max(0,start-120)+cm.start()
    s=s[:start]+s[end:]

# 이전 스타일/버튼/래퍼 제거
s=re.sub(r'<style[^>]*id="cc-live-estimate[^"]*"[^>]*>.*?</style>','',s,flags=re.I|re.S)
s=re.sub(r"<style[^>]*id='cc-live-estimate[^']*'[^>]*>.*?</style>",'',s,flags=re.I|re.S)
s=re.sub(r'<a[^>]*cc-fast-estimate[^>]*>.*?</a>','',s,flags=re.I|re.S)
s=re.sub(r'<div[^>]*cc-top-actions[^>]*>\\s*(<a\\b.*?</a>)\\s*</div>',r'\\1',s,flags=re.I|re.S)

style="""<style id="cc-live-estimate-final">
.cc-top-actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.cc-fast-estimate{display:inline-flex!important;align-items:center;justify-content:center;background:#ffcc00!important;color:#111!important;padding:11px 18px!important;border-radius:9px!important;font-weight:900!important;text-decoration:none!important}
.cc-live-wrap{max-width:920px;margin:28px auto;padding:0 20px;text-align:left}
.cc-live-box{background:#fff;border:1px solid #dbeafe;border-radius:18px;overflow:hidden;box-shadow:0 10px 30px rgba(15,23,42,.08)}
.cc-live-title{background:#0865cf;color:#fff;padding:13px 17px;font-size:18px;font-weight:900}
.cc-live-window{height:244px;overflow:hidden;background:#fff}
.cc-live-row{height:61px;display:grid;grid-template-columns:.8fr 1.15fr 1.55fr .85fr .65fr;gap:10px;align-items:center;padding:0 16px;border-bottom:1px solid #eef2f7;font-size:14px;box-sizing:border-box}
.cc-live-date{color:#0865cf;font-weight:900}.cc-live-time{color:#64748b;text-align:right}
@media(max-width:650px){.cc-top-actions{display:grid;grid-template-columns:1fr 1fr}.cc-live-row{font-size:11px;gap:5px;padding:0 8px}}
</style>"""
s=re.sub(r'</head>',style+'\\n</head>',s,count=1,flags=re.I)

# 2) 상담직통 문구가 들어간 실제 링크를 찾아 버튼 추가
button_ok=False
# 실제 <a> 내부에 span/icon 등이 있어도 보이는 글자가 "상담직통"이면 선택
for m in re.finditer(r'<a\\b[^>]*>.*?</a>',s,re.I|re.S):
    visible=re.sub(r'<[^>]+>',' ',m.group(0))
    visible=re.sub(r'\\s+',' ',visible).strip()
    if '상담직통' in visible:
        phone=m.group(0)
        fast='<a class="cc-fast-estimate" href="#estimate">⚡ 빠른 견적문의</a>'
        s=s[:m.start()]+'<div class="cc-top-actions">'+phone+fast+'</div>'+s[m.end():]
        button_ok=True
        break

# 견적 폼 앵커
if 'id="estimate"' not in s:
    s=re.sub(r'<section class="form">','<section class="form" id="estimate">',s,count=1,flags=re.I)
    s=re.sub(r'<section class="form-container">','<section class="form-container" id="estimate">',s,count=1,flags=re.I)

live="""<!-- CHANGE_CLEAN_LIVE_ESTIMATE_FINAL2 -->
<section class="cc-live-wrap"><div class="cc-live-box">
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
</script>"""

# 3) 한 개만: article형은 header 아래, 아니면 body 시작
h=re.search(r'</header>',s,re.I)
if h: s=s[:h.end()]+'\\n'+live+s[h.end():]
else:
    b=re.search(r'<body[^>]*>',s,re.I)
    if b:s=s[:b.end()]+'\\n'+live+s[b.end():]

p.write_text(s,encoding="utf-8")
print("테스트 파일:",p)
print("실시간 견적문의 최종 블록:",s.count("CHANGE_CLEAN_LIVE_ESTIMATE_FINAL2"),"개")
print("빠른 견적문의 버튼:", "성공" if button_ok else "실패")
print("백업:",bak)
print("완료 - 이 페이지 1개만 수정")
