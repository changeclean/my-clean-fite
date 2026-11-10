/* Restores original ChangeClean media and quote form on service-area pages. */
(function(){
"use strict";
function esc(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
document.addEventListener("DOMContentLoaded",function(){
const hero=document.querySelector(".hero"),footer=document.querySelector("footer");
if(!hero||!footer||document.querySelector("#cc-restored-media"))return;
const heading=document.querySelector("h1");
const area=(heading?heading.textContent:"체인지클린").trim().replace(/\\s+/g," ").slice(0,60);
const media=document.createElement("div");
media.id="cc-restored-media";
media.innerHTML='<section class="section cc-restored alt" id="cc-photos"><div class="wrap"><h2>체인지클린 청소 전후 사진</h2><p class="lede">기존 홈페이지에서 제공하던 청소 현장 사진입니다. 개별 지역 현장 사진임을 의미하지 않습니다.</p><div class="cc-media-grid"><figure><img loading="lazy" src="/assets/real-before-after-1.jpg" alt="청소 전후 사진 1"><figcaption>신발장·배수구·싱크대·창틀</figcaption></figure><figure><img loading="lazy" src="/assets/real-before-after-2.jpg" alt="청소 전후 사진 2"><figcaption>베란다·벽면 청소 전후</figcaption></figure></div></div></section><section class="section cc-restored" id="cc-videos"><div class="wrap"><h2>최근 작업 영상</h2><p class="lede">기존 체인지클린 홈페이지에 사용하던 작업 영상입니다.</p><div class="cc-videos">'+[1,2,3,4].map(n=>'<div class="cc-video-card"><video controls playsinline preload="none" poster="/cc_recent/recent_0'+n+'.webp"><source src="/cc_recent/videos10/clean_0'+n+'.mp4" type="video/mp4">영상 재생을 지원하지 않는 브라우저입니다.</video><p>현장 영상 '+n+'</p></div>').join('')+'</div></div></section>';
hero.insertAdjacentElement("afterend",media);
const reviews=document.createElement("section");
reviews.className="section cc-restored";reviews.id="customer-reviews";
reviews.innerHTML='<div class="wrap"><h2>체인지클린 고객 후기</h2><p class="lede">기존 후기 게시판과 네이버 리뷰에서 실제 고객 경험을 확인할 수 있습니다.</p><div class="cc-media-grid"><figure><img loading="lazy" src="/images/under.jpg" alt="고객 후기 안내"><figcaption>기존 고객 후기 안내 이미지</figcaption></figure><div><h3>고객 리뷰 보기</h3><p>리뷰 출처에서 고객 후기를 직접 확인해 보세요.</p><div class="cc-review-links"><a class="button" href="https://myhomecare.imweb.me/16" target="_blank" rel="noopener noreferrer">고객 후기 게시판</a><a class="button secondary" href="https://naver.me/5imyvric" target="_blank" rel="noopener noreferrer">네이버 리뷰</a></div></div></div></div>';
const quote=document.createElement("section");
quote.id="estimate";quote.className="section cc-restored cc-estimate-form";
quote.innerHTML='<div class="wrap"><div class="cc-estimate-box"><h2>간편견적 신청</h2><p class="lede">주소와 청소 날짜 등 필요한 정보를 남겨주시면 확인 후 상담드립니다.</p><form action="/thanks.html" method="POST" data-netlify="true" name="estimate"><input type="hidden" name="form-name" value="estimate"><input type="hidden" name="페이지키워드" value="'+esc(area)+'"><div class="cc-estimate-grid"><div><label for="cc-name">고객명</label><input id="cc-name" name="고객명" required></div><div><label for="cc-phone">연락처</label><input id="cc-phone" name="연락처" required type="tel"></div><div class="wide"><label for="cc-address">상세주소</label><input id="cc-address" name="상세주소" required></div><div><label for="cc-date">희망 청소날짜</label><input id="cc-date" name="청소날짜" type="date"></div><div><label for="cc-type">청소종류</label><select id="cc-type" name="청소종류"><option>입주청소</option><option>이사청소</option><option>거주청소</option><option>상가청소</option><option>사무실청소</option></select></div><div><label for="cc-shape">공간구조</label><select id="cc-shape" name="공간구조"><option>아파트</option><option>오피스텔</option><option>원룸</option><option>투룸</option><option>쓰리룸</option><option>상가</option><option>사무실</option><option>기타</option></select></div><div><label for="cc-size">청소 면적</label><input id="cc-size" name="면적" placeholder="예: 25평"></div><div class="wide"><label for="cc-notes">특이사항</label><textarea id="cc-notes" name="특이사항" placeholder="오염 상태와 요청사항을 적어주세요"></textarea></div><div class="wide"><button type="submit">견적 신청하기</button></div></div></form></div></div>';
footer.before(reviews,quote);
document.querySelectorAll('a[href="/#contact"]').forEach(a=>a.setAttribute("href","#estimate"));
const btn=document.querySelector(".hero .buttons");
if(btn){const a=document.createElement("a");a.className="button";a.href="#estimate";a.textContent="간편견적 신청";btn.prepend(a);}
});
})();
