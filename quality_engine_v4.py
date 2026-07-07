"""
quality_engine_v4.py
생성 페이지 품질검사
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List


def inspect_html(slug: str, html: str) -> Dict[str, str]:
    issues = []

    if "<title>" not in html:
        issues.append("title 없음")
    if 'name="description"' not in html:
        issues.append("description 없음")
    if 'rel="canonical"' not in html:
        issues.append("canonical 없음")
    if "application/ld+json" not in html:
        issues.append("schema 없음")
    if "<h1" not in html.lower():
        issues.append("h1 없음")
    if len(html) < 2500:
        issues.append("HTML 짧음")
    if "{{" in html and "}}" in html:
        issues.append("미치환 태그 남음")

    return {
        "slug": slug,
        "status": "OK" if not issues else "CHECK",
        "issues": " | ".join(issues),
        "length": str(len(html)),
    }


def write_quality_report(path: str | Path, rows: List[Dict[str, str]]) -> None:
    p = Path(path)
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["slug", "status", "issues", "length"])
        for r in rows:
            writer.writerow([r["slug"], r["status"], r["issues"], r["length"]])
