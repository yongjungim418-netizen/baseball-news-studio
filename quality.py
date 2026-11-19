"""뉴스 품질 필터: 스팸/알맹이 없는 기사는 버리고, 진짜 이슈 기사는 점수를 올린다."""
import re

import config


def _has(text, words):
    t = text.lower()
    return any(w.lower() in t for w in words if w)


def is_junk(title, source=""):
    t = (title or "").strip()
    if len(t) < 12:
        return True
    if _has(t, config.BLOCK_WORDS) or _has(source or "", config.BLOCK_SOURCES):
        return True
    if any(t.startswith(p) for p in config.LOW_VALUE_PREFIXES) or _has(t, config.LOW_VALUE_WORDS):
        return True
    letters = len(re.findall(r"[가-힣A-Za-z0-9]", t))
    return letters < len(t) * 0.5          # 특수문자/이모지 도배


def source_bonus(source):
    return 8 if _has(source or "", config.TRUSTED_SOURCES) else 0


def bonus(title, source=""):
    """클수록 좋은 기사"""
    b = source_bonus(source)
    b += min(sum(1 for w in config.BOOST_WORDS if w in title), 2) * 6
    if config.PREFER_WORDS and _has(title, config.PREFER_WORDS):
        b += 10
    if _has(title, config.WEAK_WORDS):
        b -= 8
    return b
