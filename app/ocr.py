import os, re, subprocess, tempfile, unicodedata
from datetime import date
from pathlib import Path
from PIL import Image
from .config import bundle_dir

AD_WORDS = (
    "PUBLICIDADE", "INFORME PUBLICITARIO", "CONTEUDO PUBLICITARIO",
    "ADVERTISEMENT", "ADVERTORIAL", "PAID CONTENT", "SPONSORED CONTENT",
)


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
    """OCR somente da zona superior para manter a busca rápida no Windows.

    O Android usa ML Kit com caixas de texto. Aqui usamos o mesmo critério de
    masthead, mas com Tesseract portátil na faixa superior da página.
    """
    exe = _tesseract_exe()
    if not exe:
        return ""
    try:
        im = Image.open(path).convert("RGB")
        # 38% cobre masthead/data e evita OCR lento da página inteira.
        h = max(1, int(im.height * 0.38))
        top = im.crop((0, 0, im.width, h))
        # O Android analisa preview ~1200 px. Fazemos o mesmo para velocidade.
        if top.width > 1400:
            nh = max(1, round(top.height * (1400 / top.width)))
            top = top.resize((1400, nh), Image.Resampling.LANCZOS)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "top.png"
            top.save(p, "PNG")
            cmd = [str(exe), str(p), "stdout", "-l", "por+eng", "--psm", "6"]
            cp = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=20,
                creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
            )
            return cp.stdout or ""
    except Exception:
        return ""


def matches_expected(text: str, name: str) -> bool:
    t = normalize(text)
    expected = normalize(name)
    if expected == "O GLOBO":
        return "O GLOBO" in t or ("GLOBO" in t and "IRINEU MARINHO" in t)
    if "FOLHA" in expected:
        return "FOLHA" in t and ("PAULO" in t or "S PAULO" in t)
    if "ESTADAO" in expected:
        return (
            "ESTADAO" in t
            or ("ESTADO" in t and "S PAULO" in t)
            or ("ESTADO" in t and "SAO PAULO" in t)
            or "FUNDADO EM 1875" in t
        )
    if "CORREIO BRAZILIENSE" in expected:
        return "CORREIO" in t and "BRAZILIENSE" in t
    if "ESTADO DE MINAS" in expected:
        return "ESTADO" in t and "MINAS" in t
    if "NEW YORK TIMES" in expected:
        return is_strong_nyt_masthead(t)
    if "WASHINGTON POST" in expected:
        return "WASHINGTON" in t and "POST" in t and "WASHINGTON POST SPORTS" not in t
    if "VALOR ECONOMICO" in expected:
        return "VALOR" in t and ("ECONOMICO" in t or "VALOR" in t)
    return bool(expected and expected in t)


def is_strong_nyt_masthead(text: str) -> bool:
    t = normalize(text)
    if "ALL THE NEWS THAT S FIT TO PRINT" in t or "ALL THE NEWS THAT IS FIT TO PRINT" in t:
        return True
    if "THE NEW YORK TIMES" not in t:
        return False
    if "THE NEW YORK TIMES COMPANY" in t and not re.search(
        r"THE NEW YORK TIMES (MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)", t
    ):
        return False
    return True


def _contains_ad(text: str) -> bool:
    t = normalize(text)
    return any(x in t for x in AD_WORDS)


def _detect_other(text: str, expected_name: str) -> str:
    t, expected = normalize(text), normalize(expected_name)
    if "O GLOBO" in t and expected != "O GLOBO": return "O GLOBO"
    if "FOLHA" in t and "PAULO" in t and "FOLHA" not in expected: return "FOLHA"
    if "CORREIO" in t and "BRAZILIENSE" in t and "CORREIO BRAZILIENSE" not in expected: return "CORREIO"
    if "ESTADO" in t and "MINAS" in t and "ESTADO DE MINAS" not in expected: return "ESTADO DE MINAS"
    if (("ESTADO" in t and "PAULO" in t) or "ESTADAO" in t) and "ESTADAO" not in expected: return "ESTADÃO"
    if "NEW YORK" in t and "TIMES" in t and "NEW YORK TIMES" not in expected: return "NYT"
    return ""


def _date_matches(text: str, target_date: date | None) -> bool:
    if not target_date:
        return False
    t = normalize(text)
    day, year = str(target_date.day), str(target_date.year)
    months_pt = ["", "JANEIRO", "FEVEREIRO", "MARCO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    months_en = ["", "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]
    return (
        re.search(rf"(?:^| )0?{re.escape(day)}(?: |$)", " " + t + " ") is not None
        and year in t
        and (months_pt[target_date.month] in t or months_en[target_date.month] in t)
    )


def score_candidate(path: Path, name: str, mastheads: list[str], target_date: date | None = None) -> tuple[int, int, str]:
    """Pontuação comparativa 0..100 alinhada ao Android v0.7.5.x."""
    text = read_top(path)
    n = normalize(text)
    try:
        im = Image.open(path)
        w, h = im.size
    except Exception:
        return 0, 0, text

    if w < 700 or h < 950 or h / max(1, w) < 1.12:
        return 0, 0, text

    expected = matches_expected(n, name)
    score = 8
    if expected:
        score += 72

    # Evidências secundárias; a presença do masthead continua dominando.
    if h > w: score += 4
    ratio = w / max(1, h)
    if 0.45 <= ratio <= 0.72: score += 5
    elif ratio <= 0.80: score += 2
    if w >= 1200 and h >= 1600: score += 5
    if _date_matches(n, target_date): score += 8

    other = _detect_other(n, name)
    if other: score -= 70

    ad = _contains_ad(n)
    if ad: score -= 10 if expected else 35

    if normalize(name).find("NEW YORK TIMES") >= 0:
        nyt_company_only = "THE NEW YORK TIMES COMPANY" in n and not is_strong_nyt_masthead(n)
        if nyt_company_only:
            score -= 45
            score = min(score, 35)

    if not expected: score = min(score, 55)
    if other: score = min(score, 20)
    if ad and not expected: score = min(score, 35)

    score = max(0, min(100, score))
    return score, score, text
