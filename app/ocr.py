import os, re, subprocess, sys, tempfile, unicodedata
from pathlib import Path
from PIL import Image
from .config import bundle_dir

AD_WORDS = ("PUBLICIDADE", "ADVERTISEMENT", "ADVERTORIAL", "INFORME PUBLICITARIO", "PATROCINADO")


def normalize(text: str) -> str:
    s = unicodedata.normalize("NFD", text or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z0-9]+", " ", s.upper()).strip()


def _tesseract_exe() -> Path | None:
    candidates = [
        bundle_dir() / "tesseract" / "tesseract.exe",
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Tesseract-OCR" / "tesseract.exe",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def read_top(path: Path) -> str:
    exe = _tesseract_exe()
    if not exe:
        return ""
    try:
        im = Image.open(path).convert("RGB")
        h = max(1, int(im.height * 0.38))
        top = im.crop((0, 0, im.width, h))
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "top.png"
            top.save(p, "PNG")
            cmd = [str(exe), str(p), "stdout", "-l", "por+eng", "--psm", "6"]
            cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                                encoding="utf-8", errors="ignore", timeout=20,
                                creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0))
            return cp.stdout or ""
    except Exception:
        return ""


def masthead_matches(text: str, mastheads: list[str]) -> int:
    content = normalize(text)
    hits = 0
    for phrase in mastheads:
        p = normalize(phrase)
        if p and p in content:
            hits += 2
            continue
        toks = [t for t in p.split() if len(t) >= 4]
        strong = sum(1 for t in toks if t in content)
        if strong >= 2:
            hits += 1
    return hits


def score_candidate(path: Path, name: str, mastheads: list[str]) -> tuple[int, int, str]:
    text = read_top(path)
    n = normalize(text)
    try:
        im = Image.open(path)
        w, h = im.size
    except Exception:
        return -10000, 0, text
    ratio = w / max(1, h)
    score = 0
    if h > w: score += 100
    if 0.45 <= ratio <= 0.72: score += 180
    elif ratio <= 0.80: score += 90
    score += min(350, (w*h)//10000)
    if w >= 1200: score += 100
    if h >= 1600: score += 100
    mh = masthead_matches(text, mastheads)
    score += mh * 1400
    if any(x in n for x in AD_WORDS): score -= 650
    if name == "THE NEW YORK TIMES":
        if re.search(r"THE NEW YORK TIMES (MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)", n):
            score += 1600
        if "THE NEW YORK TIMES COMPANY" in n and mh < 2:
            score -= 900
    confidence = max(25, min(99, 45 + mh*18 + (12 if w >= 1200 and h >= 1600 else 0) - (20 if any(x in n for x in AD_WORDS) else 0)))
    return score, confidence, text
