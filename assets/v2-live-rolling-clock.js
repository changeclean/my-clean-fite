(function () {
  "use strict";
  // The value is the actual current time in Korea, NOT a fabricated customer inquiry time.
  const formatter = new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul", hour: "2-digit", minute: "2-digit", hour12: false
  });
  function render() {
    const time = formatter.format(new Date());
    document.querySelectorAll(".cc-main-live-clock").forEach((el) => {
      el.textContent = "현재 " + time;
      el.setAttribute("aria-label", "현재 한국시간 " + time);
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render, {once:true});
  } else render();
  window.setInterval(render, 15000);
})();
