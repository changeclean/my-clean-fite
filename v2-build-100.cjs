#!/usr/bin/env node
"use strict";
/* Curated 100-area V2 pilot: retains the original blue hero, pictures,
   scrolling inquiries, contact form. Does not publish old 9,000+ pages. */
const fs=require("node:fs"),path=require("node:path");
const ROOT=__dirname,OUT=path.join(ROOT,"v2-dist");
const SITE="https://changeclean-v2-store.netlify.app";
const regions=JSON.parse(fs.readFileSync(path.join(ROOT,"v2-100-regions.json"),"utf8")).entries;
if(regions.length!==100 || new Set(regions.map(x=>x.slug)).size!==100)throw Error("Manifest must have 100 unique areas");
const sample=fs.readFileSync(path.join(ROOT,"gyeong-yongin-su-jeon-cleaning/index.html"),"utf8");
const ORIGINAL="경기 용인시 수지구 죽전동 입주청소 이사청소 체인지클린";
if(!sample.includes("CHANGE_CLEAN_V2_ROLLING_V1")||!sample.includes("3분 전")||!sample.includes("formspree.io/f/mvzlylrr"))throw Error("Reference page changed; cannot safely build");
const esc=s=>String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
const write=(p,s)=>{const full=path.join(OUT,p);fs.mkdirSync(path.dirname(full),{recursive:true});fs.writeFileSync(full,s,"utf8")};
const block=(html,start,end,value,consume=false)=>{
  const i=html.indexOf(start),j=html.indexOf(end,i+start.length);
  if(i<0||j<0)throw Error("Cannot find marker "+start.slice(0,55));
  return html.slice(0,i)+value+"\n"+html.slice(j+(consume?end.length:0));
};
const spans={
"아파트":["현관 수납장과 방·거실 걸레받이","주방 상하부장 내부와 후드 주변","욕실·베란다·창틀 레일","실외기실과 외창은 별도 작업 여부"],
"오피스텔":["복층 구조와 높은 창의 접근성","빌트인 가전 외부 및 수납장 내부","싱크대 하부·욕실 환기구","실외기실 및 옵션 가전 분해 여부"],
"원룸":["붙박이장·선반·가구 유무","작은 주방의 후드 및 싱크대","욕실 배수구와 샤워부스","짐이 있는 경우 작업 범위"],
"주거공간":["입주·이사·거주 중 청소 여부","주방·욕실·창틀 오염 상태","방·화장실 수와 평수","높은 곳·외창·특수 오염 별도 협의"]
};
const more=[
["외창도 기본 청소에 포함되나요?","외창은 실내 청소와 구분되며 접근성·안전성에 따라 가능 여부를 사전에 확인합니다."],
["이사 전날 청소가 가능한가요?","현장이 비어 있고 전기·수도 사용이 가능한지 확인하면 일정을 상담할 수 있습니다."],
["가전 분해 청소도 하나요?","에어컨·세탁기 등 분해 서비스는 별도 작업이므로 대상 제품과 날짜를 상담해 주세요."],
["집에 짐이 있어도 가능한가요?","거주 상태의 청소는 짐의 유무 및 이동 가능 여부에 따라 범위가 달라집니다."],
["사진만으로 견적을 받을 수 있나요?","공간 구조, 평수, 주방·욕실·창틀 사진을 알려주시면 사전 상담에 도움이 됩니다."],
["신축 입주청소와 구축 이사청소가 다른가요?","신축 먼지와 이전 사용 오염은 확인 포인트가 다릅니다. 실제 오염도에 따라 청소 범위를 협의합니다."],
["예약 전 확인할 사항은 무엇인가요?","희망일·상세 주소·평수·방과 욕실 수·오염도·가전 청소 여부를 알려주세요."],
["청소 후 검수는 어떻게 하나요?","주방·욕실·창틀 등 사전에 합의한 작업 범위를 중심으로 완료 상태를 확인합니다."]
];
const tip=[
"짐 반입 전 공실 상태인지 확인하면 작업 범위를 정하기 좋습니다.",
"오염도가 높은 부분은 상담 시 사진으로 먼저 공유해 주세요.",
"같은 평수라도 방·욕실 수와 내부 구조에 따라 작업량이 달라집니다.",
"입주·이사 날짜가 가까우면 청소 가능일과 전기·수도 사용 여부를 먼저 확인해 주세요.",
"수납장·붙박이장·복층 등 구조적인 특징을 알려주시면 상담이 편리합니다."
];
fs.rmSync(OUT,{recursive:true,force:true});fs.mkdirSync(OUT,{recursive:true});
function build(e,i){
let h=sample.replaceAll(ORIGINAL,e.fullname+" 입주청소 이사청소 체인지클린");
// /area/{slug}/ is two URL levels deep. Legacy ../images/ would resolve
// to /area/images/ (404); point every reused asset at the site root instead.
h=h.replace(/((?:src|href)=["\'])\.\.\/images\//g,"$1/images/");
if(/(?:src|href)=["\']\.\.\/images\//.test(h))throw Error("Broken relative image path remains: "+e.slug);
const title=e.fullname+" 입주청소·이사청소 | 범위·견적 상담 - 체인지클린";
const desc=e.fullname+" 입주청소·이사청소. "+e.kind+"의 청소 범위, 견적 준비사항, 주방·욕실·창틀 확인 포인트와 상담 신청을 안내합니다.";
const canonical=SITE+"/area/"+e.slug+"/";
h=h.replace(/<script type="application\/ld\+json">[\s\S]*?<\/script>/i,"");
h=h.replace(/<title>[\s\S]*?<\/title>/i,"<title>"+esc(title)+"</title>");
h=h.replace(/<\/head>/i,'<meta name="description" content="'+esc(desc)+'"><link rel="canonical" href="'+canonical+'"><meta property="og:title" content="'+esc(title)+'"></head>');
h=h.replace(/href="\.\/cleaning-company\/"/g,'href="/regions/"').replaceAll("우리 지역 청소업체찾기","체인지클린 지역별 청소 안내");
const checklist=spans[e.kind].map(s=>'<li>'+esc(s)+'</li>').join("");
const guide='<div style="margin:40px auto;max-width:800px;padding:25px;text-align:left;background:#f9f9f9;border-top:4px solid #007bff;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,.05)"><h2 style="color:#004080">🏠 '+esc(e.fullname)+' 청소 체크 포인트</h2><p>'+esc(e.fullname)+' '+esc(e.kind)+' 청소를 상담할 때 확인할 내용입니다. '+esc(tip[i%tip.length])+'</p><ul style="line-height:2">'+checklist+'</ul><p style="font-size:13px;color:#64748b">※ 실제 작업 범위·비용은 공간 구조와 오염도 등에 따라 달라집니다.</p></div>';
h=block(h,'<div style="margin: 40px auto; max-width: 800px; padding: 25px;','<div style="margin: 40px auto; max-width: 800px;">',guide);
const faq=[
["어떤 정보를 보내야 견적을 받을 수 있나요?","상세 주소, 면적, 방·욕실 수, 희망일, 청소 종류와 특이사항을 알려주세요."],
["기본 청소 범위는 어디까지인가요?","실내 주방·욕실·창틀 등 작업 구역을 상담 시 확인하며 외창이나 가전 분해 등의 작업은 별도 협의가 필요합니다."],
more[i%more.length],more[(i+3)%more.length],more[(i+5)%more.length]];
const faqh='<div style="margin:40px auto;max-width:800px;padding:0 20px;text-align:left"><h2 style="border-bottom:2px solid #004080;padding-bottom:10px">자주 묻는 질문 (FAQ)</h2>'+faq.map(([q,a])=>'<div class="faq-item"><h3>Q. '+esc(q)+'</h3><p>'+esc(a)+'</p></div>').join("")+'</div>';
h=block(h,'<div style="margin: 40px auto; max-width: 800px;">','<div style="margin: 40px 0; text-align: center; border-top:',faqh);
const local=regions.filter(x=>x.group===e.group&&x.slug!==e.slug);
const links=local.slice((i*3)%Math.max(1,local.length)).concat(local).slice(0,5);
const nav='<div style="margin:40px auto;max-width:800px;text-align:center;padding:20px;border-top:1px solid #ddd"><p>📍 '+esc(e.group)+' 지역별 청소 안내</p>'+links.map(x=>'<a style="margin:6px;color:#075fce" href="/area/'+x.slug+'/">'+esc(x.dong)+' 청소</a>').join(" · ")+'<p><a style="font-weight:bold;color:#004080" href="/regions/">전체 100개 지역 보기</a></p></div>';
h=block(h,'<div style="margin: 40px 0; text-align: center; border-top:','<!-- 예약폼 구역',nav);
h=h.replace('<form action="https://formspree.io/f/mvzlylrr" method="POST">','<form action="https://formspree.io/f/mvzlylrr" method="POST"><input type="hidden" name="문의지역" value="'+esc(e.fullname)+'">');
// Restore the original two-entry review presentation from the original
// Yongin Jukjeon page. Keep the original geographic reference in the
// source text; never fabricate region-specific testimonials.
const originalReviewStart='<section style="padding: 40px 20px; background: #fff; text-align: left; max-width: 800px; margin: 0 auto;">';
const originalReviewAt=sample.indexOf(originalReviewStart);
const originalReviewEnd=sample.indexOf("</section>",originalReviewAt);
if(originalReviewAt<0||originalReviewEnd<0)throw Error("Missing original review section");
let reviews=sample.slice(originalReviewAt,originalReviewEnd+"</section>".length);
// The header identifies this as a ChangeClean testimonial section, not a new
// review from the currently selected area.
reviews=reviews.replace(
  "⭐ 경기 용인시 수지구 죽전동 입주청소 이사청소 체인지클린 고객 리얼 후기",
  "⭐ 체인지클린 고객 리얼 후기"
).replace("네이버 플레이스에서 리뷰 82개 전체보기","네이버 플레이스에서 리뷰 전체보기");
h=block(h,originalReviewStart,"</section>",reviews,true);
const outsideReview=h.replace(reviews,"");
if(outsideReview.includes("경기 용인시 수지구 죽전동")||h.includes("어제 현장 피드백")||h.includes('"@type": "Review"')||!h.includes("3분 전")||!h.includes("● 견적문의")||!h.includes("★★★★★")||!h.includes("작성자: 김*호님")||!h.includes("작성자: 이*윤님"))throw Error("Quality check failed "+e.slug);
return h;
}
function hub(){
const groups=[...new Set(regions.map(r=>r.group))].map(g=>'<section><h2>'+esc(g)+'</h2><div class="grid">'+regions.filter(r=>r.group===g).map(r=>'<a href="/area/'+r.slug+'/">'+esc(r.district?r.district+" "+r.dong:r.dong)+' 입주청소</a>').join("")+'</div></section>').join("");
return '<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>체인지클린 지역별 입주청소·이사청소 100곳</title><style>body{margin:0;background:#f5f7fb;font-family:Arial,"Malgun Gothic",sans-serif}header{background:#004080;color:#fff;padding:50px 20px;text-align:center}main{max-width:1050px;margin:30px auto;padding:15px}section{background:#fff;padding:22px;margin:15px 0;border-radius:15px}h2{color:#004080}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(185px,1fr));gap:12px}.grid a{padding:13px;border:1px solid #dbe4f1;border-radius:8px;text-decoration:none;color:#075fce}p a{color:#ffcc00;font-weight:bold}</style></head><body><header><h1>체인지클린 지역별 청소 안내</h1><p>인천 · 김포 · 부천 · 고양 · 서울 · 파주 / 100개 지역</p><p><a href="tel:16886751">📞 1688-6751 상담하기</a></p></header><main>'+groups+'</main></body></html>';
}
write("_headers","/*\n  X-Robots-Tag: noindex, nofollow, noarchive\n  X-Content-Type-Options: nosniff\n");
write("_redirects","/ /gyeong-yongin-su-jeon-cleaning/ 302!\n");
write("robots.txt","User-agent: *\nAllow: /\nSitemap: "+SITE+"/sitemap.xml\n");
write("regions/index.html",hub());
write("gyeong-yongin-su-jeon-cleaning/index.html",sample.replace(/href="\.\/cleaning-company\/"/g,'href="/regions/"'));
for(let i=0;i<regions.length;i++)write("area/"+regions[i].slug+"/index.html",build(regions[i],i));
const urls=["regions/","gyeong-yongin-su-jeon-cleaning/",...regions.map(r=>"area/"+r.slug+"/")];
write("sitemap.xml",'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+urls.map(p=>'<url><loc>'+SITE+'/'+p+'</loc></url>').join("\n")+'\n</urlset>');
for(const fn of ["M2.jpg","M3.jpg","M4.jpg","M6.jpg","M7.jpg","M8.jpg","M9.jpg","M10.jpg","kaka1.jpg","banner.jpg","TEL.jpg","under.jpg"]){
const src=path.join(ROOT,"images",fn),dest=path.join(OUT,"images",fn);
if(!fs.existsSync(src))throw Error("Missing image: "+fn);
fs.mkdirSync(path.dirname(dest),{recursive:true});fs.copyFileSync(src,dest);
}
fs.mkdirSync(path.join(OUT,"assets"),{recursive:true});
fs.copyFileSync(path.join(ROOT,"assets","v2-live-rolling.css"),path.join(OUT,"assets","v2-live-rolling.css"));
if(fs.readdirSync(path.join(OUT,"area")).length!==100)throw Error("100 pages not generated");
console.log("V2 100 curated regional pages built; reference preserved; 100 pages plus hub and reference; indexing remains disabled in preview.");
