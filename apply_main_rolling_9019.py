# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(".")
PRICE_MARKER = "<!-- MAIN_PRICE_11000_V1 -->"
ROLL_MARKER = "<!-- MAIN_LIVE_ROLLING_V1 -->"

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

<section class="cc-main-live">
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

# -----------------------------------------
# 정확히 지역메인 depth 2만 수집
# 예: 지역폴더/index.html
# -----------------------------------------
targets = []

for p in ROOT.rglob("index.html"):
    try:
        rel = p.relative_to(ROOT)
    except ValueError:
        continue

    if len(rel.parts) != 2:
        continue

    try:
        s = p.read_text(encoding="utf-8")
    except Exception:
        continue

    # 우리가 방금 적용했던 11,000원 메인만 대상
    if PRICE_MARKER in s and "우리 지역 청소업체찾기" in s:
        targets.append(p)

print("적용 대상:", len(targets), "개")

# 안전장치
if len(targets) != 9019:
    raise SystemExit(
        f"중단: 예상 대상 9019개 / 실제 대상 {len(targets)}개"
    )

changed = 0
already = 0
errors = 0

for i, p in enumerate(targets, 1):

    try:
        s = p.read_text(encoding="utf-8")

        # 중복 방지
        if ROLL_MARKER in s:
            already += 1
            continue

        price_pos = s.find(PRICE_MARKER)

        if price_pos == -1:
            errors += 1
            print("가격박스 없음:", p)
            continue

        # 가격박스의 닫는 div
        end = s.find("</div>", price_pos)

        if end == -1:
            errors += 1
            print("가격박스 끝 없음:", p)
            continue

        end += len("</div>")

        # 기존 HTML은 그대로 두고 롤링만 삽입
        s = s[:end] + "\n" + rolling + "\n" + s[end:]

        p.write_text(s, encoding="utf-8")

        changed += 1

    except Exception as e:
        errors += 1
        print("오류:", p, e)

    if i % 500 == 0:
        print(
            f"[{i}/9019] "
            f"수정 {changed} / "
            f"기존 {already} / "
            f"오류 {errors}",
            flush=True
        )

print()
print("===== 완료 =====")
print("대상:", len(targets))
print("수정:", changed)
print("기존:", already)
print("오류:", errors)
