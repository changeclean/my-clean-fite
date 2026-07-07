# -*- coding: utf-8 -*-

import hashlib
import re

def fingerprint(text):
    text = re.sub(r"\s+", " ", str(text)).strip()
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def remove_duplicate_paragraphs(html):
    seen = set()
    result = []
    parts = re.split(r"(<p>.*?</p>)", html, flags=re.S)
    for part in parts:
        if part.startswith("<p>"):
            key = fingerprint(part)
            if key in seen:
                continue
            seen.add(key)
        result.append(part)
    return "".join(result)
