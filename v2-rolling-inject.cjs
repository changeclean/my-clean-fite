#!/usr/bin/env node
/**
 * ChangeClean V2: restore the classic blue scrolling inquiry panel on the
 * legacy regional-page template during the Netlify build.
 *
 * Deliberately uses clearly labelled illustrative rows.  The old production
 * code calculated "3 minutes ago" etc. from hard-coded rows, not real leads.
 * The actual Formspree endpoint must be integrated securely before displaying
 * genuinely live inquiry statuses.
 *
 * Only modifies Netlify's build checkout; main branch remains unaffected.
 */
"use strict";
const fs = require("node:fs");
const path = require("node:path");

const ROOT = __dirname;
const CSS_HREF = "/assets/v2-live-rolling.css";
const MARKER = "<!-- CHANGE_CLEAN_V2_ROLLING_V1 -->";
const examples = [
  ["01", "인천 송도동", "입주청소 · 34평", "상담 예시"],
  ["02", "김포 장기동", "이사청소 · 25평", "상담 예시"],
  ["03", "부천 중동", "입주청소 · 32평", "상담 예시"],
  ["04", "고양 일산동구", "거주청소 · 41평", "상담 예시"],
  ["05", "인천 부평구", "이사청소 · 28평", "상담 예시"],
  ["06", "서울 강서구", "입주청소 · 34평", "상담 예시"],
  ["07", "인천 계양구", "사무실청소", "상담 예시"],
  ["08", "김포 구래동", "입주청소 · 30평", "상담 예시"]
];
const row = ([id, area, service, status]) =>
  '<div class="cc-main-live-row">' +
  '<span class="cc-main-live-name">예시 ' + id + '</span>' +
  '<span class="cc-main-live-region">' + area + '</span>' +
  '<span class="cc-main-live-service">' + service + '</span>' +
  '<span class="cc-main-live-date">' + status + '</span>' +
  '</div>';
const onePass = examples.map(row).join("\n");
const WIDGET = MARKER + '\n' +
  '<section class="cc-main-live" role="region" aria-label="견적 상담 예시 롤링">' +
  '<div class="cc-main-live-head">● 견적문의 롤링' +
  '<small class="cc-main-live-caption">상담 유형 예시 · 실제 실시간 접수 내역이 아닙니다</small></div>' +
  '<a class="cc-main-live-window" href="#cc-v2-estimate-form" aria-label="견적 상담 예시를 보고 무료 견적 신청하기">' +
  '<div class="cc-main-live-track">' + onePass + onePass + '</div></a></section>';

let visited = 0, updated = 0, skipped = 0, errors = 0;
function walk(dir) {
  for (const entry of fs.readdirSync(dir, {withFileTypes: true})) {
    const fp = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if ([".git", ".github", "node_modules", "images", "assets", "cc_recent", ".netlify", "dist"].includes(entry.name)) continue;
      walk(fp);
    } else if (entry.isFile() && entry.name.toLowerCase() === "index.html") {
      visited++;
      try {
        let html = fs.readFileSync(fp, "utf8");
        if (html.includes(MARKER)) { skipped++; continue; }
        if (!/<section\s+class=["']hero-section["']/.test(html)) { skipped++; continue; }
        if (!/<section\s+class=["']form-container["']/.test(html)) { skipped++; continue; }
        const heroHeading = /(<section\s+class=["']hero-section["'][^>]*>[\s\S]*?<h1\b[^>]*>[\s\S]*?<\/h1>)/i;
        if (!heroHeading.test(html) || !/<\/head>/i.test(html)) { skipped++; continue; }
        html = html.replace(heroHeading, '$1\n' + WIDGET);
        html = html.replace(/<section\s+class=(["'])form-container\1([^>]*)>/i, (m, q, attrs) =>
          /id\s*=/.test(attrs) ? m : '<section class=' + q + 'form-container' + q + ' id="cc-v2-estimate-form"' + attrs + '>');
        if (!html.includes('href="' + CSS_HREF + '"')) {
          html = html.replace(/<\/head>/i, '<link rel="stylesheet" href="' + CSS_HREF + '">\n</head>');
        }
        fs.writeFileSync(fp, html, "utf8");
        updated++;
      } catch (e) {
        errors++;
        console.error("[rolling] failed", path.relative(ROOT, fp), e.message);
      }
    }
  }
}
walk(ROOT);
console.log("[ChangeClean V2 rolling] scanned=" + visited + " injected=" + updated + " skipped=" + skipped + " errors=" + errors);
if (errors) process.exit(1);
if (!updated && !skipped) {
  console.error("No HTML pages were scanned; check Netlify publish directory.");
  process.exit(1);
}
