import re, requests
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from .config import ACCESS_KEY

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"


def fetch_matters(apps_script_url: str, target_date: date) -> tuple[dict[str, list[str]], dict]:
    params = {"key": ACCESS_KEY, "action": "matters", "date": target_date.isoformat()}
    url = apps_script_url + ("&" if "?" in apps_script_url else "?") + urlencode(params)
    r = requests.get(url, timeout=(8, 28), headers={"User-Agent": "PrincipaisCapas-Windows/1.0"})
    r.raise_for_status()
    try:
        root = r.json()
    except Exception as exc:
        raise RuntimeError("A ponte Gmail retornou uma resposta inválida.") from exc
    if not root.get("ok"):
        raise RuntimeError(root.get("error") or "Falha na ponte Gmail")
    out: dict[str, list[str]] = {}
    for item in root.get("matters") or []:
        name = str(item.get("name") or "").strip()
        u = str(item.get("matterUrl") or "").strip()
        if not name or not u:
            continue
        out.setdefault(name, [])
        if u not in out[name] and len(out[name]) < 5:
            out[name].append(u)
    return out, root


def download_image(url: str, dest: Path, referer: str = "") -> Path:
    headers = {"User-Agent": UA, "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"}
    if referer:
        headers["Referer"] = referer
    with requests.get(url, timeout=(8, 30), headers=headers, stream=True, allow_redirects=True) as r:
        r.raise_for_status()
        ctype = (r.headers.get("Content-Type") or "").lower()
        if "html" in ctype:
            raise RuntimeError("O endereço retornou HTML em vez da imagem da página.")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(128 * 1024):
                if chunk:
                    f.write(chunk)
    return dest


def safe_slug(name: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "capa"
