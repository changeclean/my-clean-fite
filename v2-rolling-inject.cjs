#!/usr/bin/env node
/**
 * ChangeClean V2: restore the classic blue scrolling inquiry panel on the
 * legacy regional-page template during the Netlify build.
 *
 * Uses the legacy visual's static scrolling pseudonyms and relative time labels.
 * This is presentation content, not a real-time feed.
 *
 * Only modifies Netlify's build checkout; main branch remains unaffected.
 */
"use strict";
const fs = require("node:fs");
const path = require("node:path");

const ROOT = __dirname;
const CSS_HREF = "/assets/v2-live-rolling.css";
const MARKER = "<!-- CHANGE_CLEAN_V2_ROLLING_V1 -->";
const regions = [
  ["최*석", "인천 송도동", "입주청소 · 34평", "3분 전"],
  ["김*영", "김포 장기동", "이사청소 · 25평", "8분 전"],
  ["박*민", "부천 중동", "입주청소 · 32평", "14분 전"],
  ["이*희", "고양 일산동구", "거주청소 · 41평", "21분 전"],
  ["정*호", "인천 부평구", "이사청소 · 28평", "37분 전"],
  ["한*진", "서울 강서구", "입주청소 · 34평", "48분 전"],
  ["오*현", "인천 계양구", "사무실청소", "1시간 전"],
  ["강*은", "김포 구래동", "입주청소 · 30평", "1시간 전"]
];
const row = ([id, area, service, ago]) =>
  '<div class="cc-main-live-row">' +
  '<span class="cc-main-live-name">' + id + '</span>' +
  '<span class="cc-main-live-region">' + area + '</span>' +
  '<span class="cc-main-live-service">' + service + '</span>' +
  '<span class="cc-main-live-time">' + ago + '</span>' +
  '</div>';
const onePass = regions.map(row).join("\n");
const WIDGET = MARKER + '\n' +
  '<section class="cc-main-live" role="region" aria-label="견적 문의 항목">' +
  '<div class="cc-main-live-head">● 견적문의' +
  '</div>' +
  '<a class="cc-main-live-window" href="#cc-v2-estimate-form" aria-label="견적 문의 항목을 보고 무료 견적 신청하기">' +
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
