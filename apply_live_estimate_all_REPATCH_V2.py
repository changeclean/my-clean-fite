# -*- coding: utf-8 -*-
from pathlib import Path
import argparse, shutil, re
MARK="CHANGE_CLEAN_LIVE_ESTIMATE_V2"
CSS='<style id="cc-live-estimate-style">\n.cc-top-actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap}\n.cc-fast-estimate{display:inline-flex;align-items:center;justify-content:center;background:#ffcc00!important;color:#111!important;padding:11px 18px;border-radius:28px;font-weight:900;text-decoration:none}\n.cc-live-wrap{max-width:920px;margin:28px auto;padding:0 20px;text-align:left}\n.cc-live-box{background:#fff;border:1px solid #dbeafe;border-radius:18px;overflow:hidden;box-shadow:0 10px 30px rgba(15,23,42,.08)}\n.cc-live-title{background:#0865cf;color:#fff;padding:13px 17px;font-size:18px;font-weight:900}\n.cc-live-window{height:244px;overflow:hidden}.cc-live-track{will-change:transform}\n.cc-live-row{height:61px;display:grid;grid-template-columns:.8fr 1.15fr 1.55fr .85fr .65fr;gap:10px;align-items:center;padding:0 16px;border-bottom:1px solid #eef2f7;font-size:14px}\n.cc-live-row b{font-weight:900}.cc-live-date{color:#0865cf;font-weight:900}.cc-live-time{color:#64748b;text-align:right}\n@media(max-width:650px){.cc-top-actions{display:grid;grid-template-columns:1fr 1fr;width:100%;gap:7px}.cc-top-actions>a{margin:0!important;padding:10px 7px!important;font-size:13px!important;text-align:center}.cc-live-wrap{padding:0 12px;margin:20px auto}.cc-live-row{grid-template-columns:.72fr 1.05fr 1.35fr .8fr .62fr;gap:5px;padding:0 9px;font-size:11.5px}}\n</style>'
LIVE='<!-- CHANGE_CLEAN_LIVE_ESTIMATE_V2 -->\n<section class="cc-live-wrap" aria-label="실시간 견적문의"><div class="cc-live-box"><div class="cc-live-title">● 실시간 견적문의</div><div class="cc-live-window"><div class="cc-live-track" id="ccLiveTrack"></div></div></div></section>\n<script>\n(function(){const names=["최*석","김*영","박*민","이*희","정*훈","한*진","윤*호","조*현","강*우","문*정","송*연","오*준"],areas=["인천 송도동","김포 장기동","부천 중동","고양 일산동구","인천 부평동","서울 송파구","인천 청라동","김포 구래동","부천 상동","고양 덕양구"],services=["입주청소 · 34평","이사청소 · 25평","입주청소 · 32평","거주청소 · 41평","이사청소 · 28평","입주청소 · 24평","오피스텔 · 18평","입주청소 · 36평"],mins=[3,8,14,21,29,37,46,58,72,89,105,128],today=new Date();today.setHours(0,0,0,0);const md=d=>(d.getMonth()+1)+"/"+d.getDate(),rows=[];for(let i=0;i<12;i++){let d=new Date(today);d.setDate(d.getDate()+2+((i*3)%18));rows.push([names[i%names.length],areas[i%areas.length],services[i%services.length],"예약 "+md(d),mins[i]+"분 전"])}const t=document.getElementById("ccLiveTrack");if(!t)return;rows.concat(rows.slice(0,4)).forEach(r=>{let e=document.createElement("div");e.className="cc-live-row";e.innerHTML="<b>"+r[0]+"</b><span>"+r[1]+"</span><span>"+r[2]+"</span><span class=\'cc-live-date\'>"+r[3]+"</span><span class=\'cc-live-time\'>"+r[4]+"</span>";t.appendChild(e)});let i=0;setInterval(()=>{i++;t.style.transition="transform .8s ease";t.style.transform="translateY("+(-61*i)+"px)";if(i>=rows.length)setTimeout(()=>{t.style.transition="none";i=0;t.style.transform="translateY(0)"},850)},3200)})();\n</script>'
def patch(p):
    s=p.read_text(encoding="utf-8",errors="ignore"); old=s
    if 'id="cc-live-estimate-style"' not in s:s=s.replace("</head>",CSS+"\n</head>",1)
    if 'property="og:image"' not in s:
        img="https://clever-griffin-93819d.netlify.app/assets/hero-card-hand.jpg"
        s=s.replace("</head>",f'<meta property="og:image" content="{img}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{img}"></head>',1)
    if "cc-fast-estimate" not in s:
        # 하루 50개 게시글 템플릿: 상담직통 버튼 옆
        direct='<a class="direct" href="tel:01068113176">상담직통 010-6811-3176</a>'
        if direct in s:
            s=s.replace(direct,'<div class="cc-top-actions">'+direct+'<a class="cc-fast-estimate" href="#estimate">⚡ 빠른 견적문의</a></div>',1)
            s=s.replace('<section class="form">','<section class="form" id="estimate">',1)
        x='<a class="topcall" href="tel:16886751">☎ 1688-6751</a>'
        if "cc-fast-estimate" not in s and x in s:s=s.replace(x,'<div class="cc-top-actions">'+x+'<a class="cc-fast-estimate" href="#estimate">⚡ 빠른 견적문의</a></div>',1)
        elif 'class="hero-section"' in s:
            q=s.find("</section>",s.find('class="hero-section"'))
            c='<div class="cc-top-actions" style="justify-content:center;margin-top:18px"><a style="background:#fff;color:#004080;padding:11px 18px;border-radius:28px;font-weight:900;text-decoration:none" href="tel:01068113176">☎ 상담직통 010-6811-3176</a><a class="cc-fast-estimate" href="#cc-estimate-form">⚡ 빠른 견적문의</a></div>'
            s=s[:q]+c+s[q:];s=s.replace('<section class="form-container">','<section class="form-container" id="cc-estimate-form">',1)
    if MARK not in s:
        # 하루 50개 게시글 유형은 header 바로 아래에 삽입
        mh=re.search(r"</header>",s,re.I)
        if mh:
            s=s[:mh.end()]+"\n"+LIVE+s[mh.end():]
        else:
            st=s.find('class="hero-grid"') if 'class="hero-grid"' in s else s.find('class="hero-section"')
            q=s.find("</section>",st) if st!=-1 else -1
            if q!=-1:
                q+=10;s=s[:q]+"\n"+LIVE+s[q:]
            else:
                mb=re.search(r"<body[^>]*>",s,re.I)
                if mb:s=s[:mb.end()]+"\n"+LIVE+s[mb.end():]
    if s!=old:p.write_text(s,encoding="utf-8");return 1
    return 0
ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");ap.add_argument("--dry-run",action="store_true");a=ap.parse_args()
root=Path(a.root).resolve()
targets=[]
for p in root.rglob("*.html"):
    if ".git" in p.parts:continue
    t=p.read_text(encoding="utf-8",errors="ignore")
    if "<html" in t.lower() and ("체인지클린" in t or "{{KEYWORD}}" in t):targets.append(p)
print(f"대상 HTML: {len(targets):,}개")
if a.dry_run:
    print("실제 수정 없음");[print("-",p.relative_to(root)) for p in targets[:20]]
else:
    b=root.parent/(root.name+"_backup_before_live_estimate")
    if not b.exists():print("백업 생성:",b);shutil.copytree(root,b,ignore=shutil.ignore_patterns(".git"))
    n=0
    for i,p in enumerate(targets,1):
        n+=patch(p)
        if i%250==0 or i==len(targets):print(f"[{i:,}/{len(targets):,}] 수정 {n:,}개")
    print(f"완료: {n:,}개 수정")
    print("확인 후: git add .  /  git commit -m \"실시간 견적문의 전체 적용\"  /  git push")
