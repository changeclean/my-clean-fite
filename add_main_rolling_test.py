# -*- coding: utf-8 -*-
from pathlib import Path

p = Path("main_rolling_test.html")
s = p.read_text(encoding="utf-8")

MARKER = "<!-- MAIN_LIVE_ROLLING_V1 -->"

if MARKER in s:
    raise SystemExit("이미 롤링박스가 들어가 있습니다.")

# 평당 11,000원 박스의 마커를 기준으로 찾음
PRICE_MARKER = "<!-- MAIN_PRICE_11000_V1 -->"

pos = s.find(PRICE_MARKER)
if pos == -1:
    raise SystemExit("평당 11,000원 박스를 찾지 못했습니다.")

# 가격박스의 닫는 div 위치
end = s.find("</div>", pos)
if end == -1:
    raise SystemExit("가격박스 끝을 찾지 못했습니다.")

end += len("</div>")

rolling = r'''
<!-- MAIN_LIVE_ROLLING_V1 -->
<style>
.cc-main-live{
    max-width:760px;
    margin:18px auto 26px;
    border:1px solid #dbeafe;
    border-radius:16px;
    overflow:hidden;
    background:#fff;
    box-shadow:0 8px 24px rgba(15,23,42,.07);
}
.cc-main-live-head{
    background:#075fce;
    color:#fff;
    padding:13px 17px;
    font-size:18px;
    font-weight:900;
}
.cc-main-live-window{
    height:244px;
    overflow:hidden;
    cursor:pointer;
}
.cc-main-live-track{
    animation:ccMainScroll 28s linear infinite;
}
.cc-main-live-row{
    height:61px;
    display:grid;
    grid-template-columns:70px 1.15fr 1.4fr 85px 65px;
    gap:8px;
    align-items:center;
    padding:0 14px;
    border-bottom:1px solid #eef2f7;
    font-size:13px;
}
.cc-main-live-name{font-weight:900}
.cc-main-live-date{
    color:#075fce;
    font-weight:800;
    white-space:nowrap;
}
.cc-main-live-time{
    color:#64748b;
    text-align:right;
    white-space:nowrap;
}
@keyframes ccMainScroll{
    from{transform:translateY(0)}
    to{transform:translateY(-488px)}
}
@media(max-width:600px){
    .cc-main-live-row{
        grid-template-columns:55px 1fr 72px 55px;
        padding:0 8px;
        gap:5px;
        font-size:11px;
    }
    .cc-main-live-service{display:none}
}
</style>

<section class="cc-main-live" id="cc-main-live">
    <div class="cc-main-live-head">● 실시간 견적문의</div>
    <div class="cc-main-live-window" id="ccMainLiveWindow">
        <div class="cc-main-live-track" id="ccMainLiveTrack"></div>
    </div>
</section>

<script>
(function(){
    const data=[
        ["최*석","인천 송도동","입주청소 · 34평",3,3],
        ["김*영","김포 장기동","이사청소 · 25평",6,8],
        ["박*민","부천 중동","입주청소 · 32평",9,14],
        ["이*희","고양 일산동구","거주청소 · 41평",13,21],
        ["정*호","인천 부평구","이사청소 · 28평",17,37],
        ["한*진","서울 강서구","입주청소 · 34평",21,48],
        ["오*현","인천 계양구","사무실청소",25,62],
        ["강*은","김포 구래동","입주청소 · 30평",29,78]
    ];

    const today=new Date();
    today.setHours(0,0,0,0);

    const fmt=d => (d.getMonth()+1)+"/"+d.getDate();

    const rows=data.map(x=>{
        const d=new Date(today);
        d.setDate(d.getDate()+x[3]);

        const ago=x[4]<60
            ? x[4]+"분 전"
            : Math.floor(x[4]/60)+"시간 전";

        return `
        <div class="cc-main-live-row">
            <span class="cc-main-live-name">${x[0]}</span>
            <span>${x[1]}</span>
            <span class="cc-main-live-service">${x[2]}</span>
            <span class="cc-main-live-date">예약 ${fmt(d)}</span>
            <span class="cc-main-live-time">${ago}</span>
        </div>`;
    }).join("");

    const track=document.getElementById("ccMainLiveTrack");
    if(track) track.innerHTML=rows+rows;

    /* 클릭하면 이 메인페이지의 청소업체찾기 링크로 이동 */
    const win=document.getElementById("ccMainLiveWindow");

    if(win){
        win.addEventListener("click", function(){
            const links=[...document.querySelectorAll("a")];

            const target=links.find(a =>
                (a.textContent || "").includes("우리 지역 청소업체찾기")
            );

            if(target) target.click();
        });
    }
})();
</script>
'''

s = s[:end] + "\n" + rolling + "\n" + s[end:]

p.write_text(s, encoding="utf-8")

print("완료")
print("파일:", p.resolve())
print("롤링박스:", s.count(MARKER), "개")
print("기존 본문은 삭제하거나 교체하지 않았습니다.")