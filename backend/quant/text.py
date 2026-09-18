from __future__ import annotations
import re
from collections.abc import Iterable

_WORD = re.compile(r"[a-z0-9]{2,}")
_STOP = frozenset({
    "the","and","for","with","that","this","from","into","about","after","before","your","you","are","was","were",
    "have","has","had","its","their","they","them","our","out","new","now","just","but","not","who","what","when",
    "where","why","how","can","could","would","should","will","https","www","com","amp","via","more","most"
})

def tokens(text: str, limit: int = 28) -> frozenset[str]:
    found=[]
    for word in _WORD.findall(text.lower()):
        if word in _STOP: continue
        found.append(word)
        if len(found) >= limit: break
    return frozenset(found)

def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa=set(a); sb=set(b)
    if not sa or not sb: return 0.0
    return len(sa & sb) / len(sa | sb)

def canonical_label(title: str, text: str = "") -> str:
    ordered=[]; seen=set()
    for word in _WORD.findall((title+" "+text).lower()):
        if word in _STOP or word in seen: continue
        seen.add(word); ordered.append(word)
        if len(ordered) == 5: break
    return " ".join(ordered) or "emerging signal"

def memeability_heuristic(title: str, text: str) -> float:
    combined=f"{title} {text}".lower(); words=_WORD.findall(combined); score=45.0
    if 1 <= len(title.split()) <= 5: score += 16
    if any(x in combined for x in ("meme","clip","reaction","dog","cat","robot","ai","viral","joke","mascot")): score += 17
    if any(ch.isdigit() for ch in title): score += 3
    if len(words) <= 45: score += 6
    if any(x in combined for x in ("report","earnings","regulation","lawsuit")): score -= 12
    return max(0.0,min(100.0,score))
