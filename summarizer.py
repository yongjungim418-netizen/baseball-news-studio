"""카드용 한국어 요약. ANTHROPIC_API_KEY 가 있으면 Claude 로, 없으면 RSS 문구 그대로 사용."""
import json
import os
import re
import urllib.request

import config


def _fallback(title, snippet):
    lines = []
    if snippet and snippet.strip() != title.strip() and len(snippet) > 25:
        for s in re.split(r"(?<=[.!?다])\s+", snippet):
            s = s.strip()
            if len(s) > 8:
                lines.append(s[:70])
            if len(lines) == 3:
                break
    return {"title": title, "lines": lines}


def summarize(title, snippet, source):
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return _fallback(title, snippet)
    prompt = (
        "아래 야구 기사의 제목과 요약문만 근거로, 인스타 카드뉴스용 내용을 만들어줘.\n"
        "- title: 한국어 제목 (원문이 한국어면 그대로, 외국어면 번역, 40자 이내)\n"
        "- lines: 핵심 요약 최대 3줄 (각 45자 이내). 제공된 정보에 없는 내용은 절대 추가하지 마.\n"
        "- 요약할 근거가 부족하면 lines 는 빈 배열.\n"
        'JSON 객체만 출력: {"title": "...", "lines": ["..."]}\n\n'
        f"제목: {title}\n요약문: {snippet}\n출처: {source}"
    )
    body = json.dumps({"model": config.ANTHROPIC_MODEL, "max_tokens": 400,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            text = json.loads(r.read())["content"][0]["text"]
        data = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
        return {"title": data.get("title") or title, "lines": [str(x) for x in data.get("lines", [])][:3]}
    except Exception:
        return _fallback(title, snippet)
