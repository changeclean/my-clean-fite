# -*- coding: utf-8 -*-
from pathlib import Path

p = Path("recovery_live_test.html")
s = p.read_text(encoding="utf-8")

MARKER = "<!-- LIVE_ESTIMATE_SAFE_TEST -->"

# 중복 실행 방지
if MARKER in s:
    raise SystemExit("이미 실시간 견적문의가 들어가 있습니다.")

# '우리 지역 청소업체찾기' 링크의 시작 위치 찾기
text_pos = s.find("우리 지역 청소업체찾기")
if text_pos == -1:
    raise SystemExit("우리 지역 청소업체찾기 문구를 찾지 못했습니다.")

anchor_pos = s.rfind("<a ", 0, text_pos)
if anchor_pos == -1:
    raise SystemExit("청소업체찾기 링크 시작점을 찾지 못했습니다.")

live = r'''
<!-- LIVE_ESTIMATE_SAFE_TEST -->
<style>
.cc-live-safe{
    max-width:920px;
    margin:28px auto;
    padding:0 20px;
    box-sizing:border-box;
}
.cc-live-safe-box{
    background:#fff;
    border:1px solid #dbeafe;
    border-radius:18px;
    overflow:hidden;
    box-shadow:0 10px 30px rgba(15,23,42,.08);
}
.cc-live-safe-title{
    background:#0865cf;
    color:#fff;
    padding:14px 17px;
    font-size:18px;
    font-weight:900;
}
.cc-live-safe-window{
    height:244px;
    overflow:hidden;
}
.cc-live-safe-list{
    transition:transform .8s ease;
}
.cc-live-safe-row{
    height:61px;
    display:grid;
    grid-template-columns:.8fr 1.15fr 1.55fr .85fr .65fr;
    gap:10px;
    align-items:center;
    padding:0 16px;
    border-bottom:1px solid #eef2f7;
    font-size:14px;
    box-sizing:border-box;
}
.cc-live-safe-date{
    color:#0865cf;
    font-weight:900;
}
.cc-live-safe-time{
    color:#64748b;
    text-align:right;
}
@media(max-width:650px){
    .cc-live-safe-row{
        font-size:11px;
        gap:5px;
        padding:0 8px;
    }
}
</style>

<section class="cc-live-safe">
  <div class="cc-live-safe-box">
    <div class="cc-live-safe-title">● 실시간 견적문의</div>
    <div class="cc-live-safe-window">
      <div class="cc-live-safe-list" id="ccLiveSafeList"></div>
    </div>
  </div>
</section>

<script>
(function(){
    const data = [
        ["최*석","인천 송도동","입주청소 · 34평","3분 전"],
        ["김*영","김포 장기동","이사청소 · 25평","8분 전"],
        ["박*민","부천 중동","입주청소 · 32평","14분 전"],
        ["이*희","고양 일산동구","거주청소 · 41평","21분 전"],
        ["정*훈","인천 부평동","이사청소 · 28평","29분 전"],
        ["한*진","서울 송파구","입주청소 · 24평","37분 전"]
    ];

    const target = document.getElementById("ccLiveSafeList");
    if(!target) return;

    const now = new Date();

    data.forEach(function(r,i){
        const d = new Date(now);
        d.setDate(d.getDate() + 2 + i*3);

        const row = document.createElement("div");
        row.className = "cc-live-safe-row";

        row.innerHTML =
            "<b>"+r[0]+"</b>" +
            "<span>"+r[1]+"</span>" +
            "<span>"+r[2]+"</span>" +
            "<span class='cc-live-safe-date'>예약 "+
            (d.getMonth()+1)+"/"+d.getDate()+
            "</span>" +
            "<span class='cc-live-safe-time'>"+r[3]+"</span>";

        target.appendChild(row);
    });

    let n = 0;

    setInterval(function(){
        n = (n + 1) % 3;
        target.style.transform = "translateY(" + (-61*n) + "px)";
    },3200);
})();
</script>

'''

# 기존 HTML은 그대로 두고 앞에 추가만 함
s = s[:anchor_pos] + live + s[anchor_pos:]

p.write_text(s, encoding="utf-8")

print("완료")
print("파일:", p.resolve())
print("견적문의 블록:", s.count(MARKER), "개")
print("기존 본문은 삭제하지 않았습니다.")