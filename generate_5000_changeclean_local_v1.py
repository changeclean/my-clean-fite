# -*- coding: utf-8 -*-
from pathlib import Path
import argparse, hashlib, html, random, re, subprocess

ROOT=Path(".")
DOMAIN="https://clever-griffin-93819d.netlify.app"
OG_IMAGE=DOMAIN+"/images/M2.jpg"

AREAS=[
("인천","중구",["중산동","운서동","운남동","영종동","신흥동","항동","신포동"]),
("인천","동구",["송현동","송림동","화수동","만석동"]),
("인천","미추홀구",["주안동","도화동","용현동","학익동","숭의동","문학동"]),
("인천","연수구",["송도동","연수동","동춘동","옥련동","청학동","선학동"]),
("인천","남동구",["구월동","간석동","논현동","만수동","서창동","장수동","도림동"]),
("인천","부평구",["부평동","산곡동","청천동","갈산동","삼산동","십정동","일신동","부개동"]),
("인천","계양구",["계산동","작전동","효성동","박촌동","동양동","귤현동","임학동"]),
("인천","서구",["청라동","가정동","석남동","가좌동","검암동","경서동","당하동","마전동","원당동","불로동"]),
("부천","원미구",["중동","상동","심곡동","원미동","춘의동","도당동","약대동","소사동"]),
("부천","소사구",["괴안동","범박동","옥길동","송내동","심곡본동"]),
("부천","오정구",["원종동","고강동","오정동","삼정동","내동","여월동"]),
("김포","김포시",["고촌읍","풍무동","사우동","북변동","걸포동","장기동","운양동","구래동","마산동","양촌읍","통진읍"]),
("고양","덕양구",["화정동","행신동","원흥동","삼송동","지축동","향동동","덕은동","성사동","주교동"]),
("고양","일산동구",["백석동","마두동","장항동","정발산동","풍동","식사동","중산동"]),
("고양","일산서구",["주엽동","대화동","탄현동","일산동","가좌동","덕이동"]),
("시흥","시흥시",["배곧동","정왕동","은행동","대야동","신천동","능곡동","장곡동","목감동"]),
("안산","상록구",["본오동","사동","이동","성포동","월피동","수암동"]),
("안산","단원구",["고잔동","초지동","선부동","원곡동","와동","신길동"]),
("서울","강서구",["마곡동","가양동","등촌동","화곡동","방화동","공항동"]),
("서울","양천구",["목동","신정동","신월동"])
]
SERVICES=["입주청소","이사청소","거주청소","아파트청소","오피스텔청소","원룸청소","투룸청소","상가청소","사무실청소","폐기물청소"]
INTENTS=[
"{area} {service}","{area} {service} 업체","{area} {service} 가격","{area} {service} 비용",
"{area} {service} 견적","{area} {service} 잘하는곳","{area} {service} 전문업체",
"{area} {service} 추천","{area} {service} 평당 가격","{area} {service} 평당 11000원",
"{area} 24평 {service}","{area} 25평 {service}","{area} 30평 {service}",
"{area} 32평 {service}","{area} 34평 {service}","{area} 40평 {service}",
"{area} 아파트 {service}","{area} 오피스텔 {service}","{area} 원룸 {service}",
"{area} 이사 전 {service}","{area} 입주 전 {service}","{area} 청소업체 견적","{area} 청소업체 가격"
]

def slugify(text):
    mp={"인천":"incheon","부천":"bucheon","김포":"gimpo","고양":"goyang","시흥":"siheung","안산":"ansan","서울":"seoul",
        "입주청소":"movein-cleaning","이사청소":"move-cleaning","거주청소":"residential-cleaning",
        "아파트청소":"apartment-cleaning","오피스텔청소":"officetel-cleaning","원룸청소":"oneroom-cleaning",
        "투룸청소":"tworoom-cleaning","상가청소":"shop-cleaning","사무실청소":"office-cleaning","폐기물청소":"waste-cleaning"}
    x=text
    for k,v in mp.items(): x=x.replace(k,v)
    x=re.sub(r"[^a-zA-Z0-9가-힣]+","-",x).strip("-")
    x=re.sub(r"[가-힣]+","local",x).lower()
    x=re.sub(r"-+","-",x).strip("-")
    return x[:82]+"-"+hashlib.md5(text.encode()).hexdigest()[:8]

def pool():
    a=[]
    seen=set()
    for city,gu,dongs in AREAS:
        for dong in dongs:
            area=f"{city} {gu} {dong}" if gu not in (city,"김포시","시흥시") else f"{city} {dong}"
            for service in SERVICES:
                for p in INTENTS:
                    kw=p.format(area=area,service=service)
                    if kw not in seen:
                        seen.add(kw); a.append((area,service,kw))
    random.Random(11000).shuffle(a)
    return a

def make_page(T,row):
    area,service,kw=row
    folder=ROOT/("seo-"+slugify(kw))
    canonical=f"{DOMAIN}/{folder.name}/"
    title=f"{kw} | 평당 11,000원 체인지클린"
    desc=f"{kw} 알아보기. 체인지클린 청소비용 평당 11,000원 기준, 청소범위·전후사진·간편견적을 확인하세요."
    s=T
    s=re.sub(r"<title>.*?</title>",f"<title>{html.escape(title)}</title>",s,count=1)
    s=re.sub(r'<meta name="description" content=".*?">',f'<meta name="description" content="{html.escape(desc)}">',s,count=1)
    s=re.sub(r'<link rel="canonical" href=".*?">',f'<link rel="canonical" href="{canonical}">',s,count=1)
    s=re.sub(r'<meta property="og:image" content=".*?">',f'<meta property="og:image" content="{OG_IMAGE}">',s,count=1)
    s=re.sub(r'<meta name="twitter:image" content=".*?">',f'<meta name="twitter:image" content="{OG_IMAGE}">',s,count=1)
    s=s.replace('src="assets/','src="../assets/')
    s=s.replace("인천 입주청소",kw)
    s=re.sub(r'<h1>.*?</h1>',f'<h1>{html.escape(kw)}<br><em>평당 11,000원부터 간편견적</em></h1>',s,count=1,flags=re.S)
    price=f'''<section style="padding:20px 0 8px"><div class="wrap"><div style="max-width:920px;margin:auto;background:#fff8e8;border:2px solid #ffcc00;border-radius:18px;padding:20px;text-align:center"><b>{html.escape(area)} {html.escape(service)} 비용 안내</b><div style="font-size:30px;font-weight:900;color:#0759bd">청소비용 평당 11,000원</div><div>현장 구조·오염도·추가 작업에 따라 최종 견적은 달라질 수 있습니다.</div></div></div></section>'''
    s=s.replace("<main>","<main>\n"+price,1)
    s=re.sub(r'<input type="hidden" name="페이지키워드" value=".*?">',f'<input type="hidden" name="페이지키워드" value="{html.escape(kw)}">',s,count=1)
    faq=f'''<div class="faq-box"><div class="faq-item"><h3>Q: {html.escape(area)} {html.escape(service)} 비용은?</h3><p>A: 기본 안내가는 평당 11,000원이며 현장 구조, 오염도, 추가 작업 여부에 따라 최종 견적이 달라질 수 있습니다.</p></div><div class="faq-item"><h3>Q: {html.escape(area)} 방문 상담이 가능한가요?</h3><p>A: 주소, 평수, 구조와 현장 사진을 보내주시면 필요한 청소 범위와 일정을 확인해 상담드립니다.</p></div></div>'''
    s=re.sub(r'<div class="faq-box">.*?</div></div><div class="page-nav">',faq+'<div class="page-nav">',s,count=1,flags=re.S)
    return folder,folder/"index.html",s,canonical

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--count",type=int,default=10)
    ap.add_argument("--start",type=int,default=0)
    ap.add_argument("--no-git",action="store_true")
    args=ap.parse_args()
    tp=ROOT/"미리보기.html"
    if not tp.exists(): raise SystemExit("미리보기.html을 같은 폴더에 두세요.")
    T=tp.read_text(encoding="utf-8")
    rows=pool()[args.start:args.start+args.count]
    if len(rows)<args.count: raise SystemExit("생성 후보가 부족합니다.")
    made=[]; urls=[]
    for i,row in enumerate(rows,1):
        folder,path,s,url=make_page(T,row)
        if path.exists():
            print(f"[{i}/{len(rows)}] 기존: {path}"); continue
        folder.mkdir(parents=True,exist_ok=True)
        path.write_text(s,encoding="utf-8",newline="\n")
        made.append(path); urls.append(url)
        print(f"[{i}/{len(rows)}] {path}")
    sm=ROOT/"sitemap_5000_local.txt"
    old=sm.read_text(encoding="utf-8").splitlines() if sm.exists() else []
    sm.write_text("\n".join(dict.fromkeys(old+urls))+"\n",encoding="utf-8")
    print("\n===== 완료 =====")
    print("신규:",len(made))
    print("검색화면 가격: 평당 11,000원")
    print("검색/공유 이미지:",OG_IMAGE)
    if made: print("첫 파일:",made[0])
    if made and not args.no_git:
        subprocess.run(["git","add","-A"],check=True)
        subprocess.run(["git","commit","-m",f"Add {len(made)} local cleaning long-tail pages"],check=True)
        print("커밋 완료 / push는 직접: git push origin main")

if __name__=="__main__":
    main()
