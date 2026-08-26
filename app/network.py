import re
import requests
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from .config import ACCESS_KEY

ANDROID_FEED_UA = "PrincipaisCapas/0.7.0 Android"
IMAGE_UA = "Mozilla/5.0 (Android) PrincipaisCapas/0.7.5.0"


def _valid_webapp_url(url: str) -> bool:
    u = (url or "").strip().lower()
    return u.startswith("https://script.google.com/macros/s/") and "/exec" in u


def fetch_matters(apps_script_url: str, target_date: date) -> tuple[dict[str, list[str]], dict]:
    """Port do ClippingFeedClient.fetchMatterUrls do Android.

    Mesmos parâmetros, chave, data yyyy-MM-dd, redirects e limites de timeout.
    Mantém todas as matterUrl únicas retornadas pelo Apps Script.
    """
    base = (apps_script_url or "").strip()
    if not base:
        raise RuntimeError("Gmail automático não configurado")
    if not _valid_webapp_url(base):
        raise RuntimeError("URL inválida do Apps Script")

    params = {"key": ACCESS_KEY, "action": "matters", "date": target_date.isoformat()}
    url = base + ("&" if "?" in base else "?") + urlencode(params)

    session = requests.Session()
    # requests já usa proxy do ambiente. No Windows, urllib também pode ler a
    # configuração de proxy do sistema; trust_env precisa permanecer ativado.
    session.trust_env = True
    try:
        r = session.get(
            url,
            timeout=(7, 25),
            headers={"User-Agent": ANDROID_FEED_UA},
            allow_redirects=True,
        )
    except requests.Timeout as exc:
        raise RuntimeError("Ponte Gmail excedeu o tempo de resposta") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"Ponte Gmail: {exc}") from exc

    if r.status_code < 200 or r.status_code >= 300:
        raise RuntimeError(f"Ponte Gmail HTTP {r.status_code}")

    body = (r.text or "").strip()
    low = body[:120].lower()
    if low.startswith("<!doctype") or low.startswith("<html"):
        raise RuntimeError(
            "A ponte abriu HTML. Atualize a implantação do Apps Script e mantenha acesso como Qualquer pessoa."
        )
    try:
        root = r.json()
    except Exception as exc:
        raise RuntimeError("Resposta inválida da ponte Gmail") from exc
    if not root.get("ok"):
        raise RuntimeError(root.get("error") or "Falha na ponte Gmail")

    out: dict[str, list[str]] = {}
    for item in root.get("matters") or []:
        name = str(item.get("name") or "").strip()
        matter_url = str(item.get("matterUrl") or "").strip()
        if not name or not matter_url:
            continue
        arr = out.setdefault(name, [])
        if matter_url not in arr:
            arr.append(matter_url)

    if not out:
        threads = int(root.get("threads") or 0)
        messages = int(root.get("messagesScanned") or 0)
        raw_links = int(root.get("rawLeiaMaisFound") or 0)
        dated = int(root.get("datedItemsMatched") or 0)
        if threads == 0 or messages == 0:
            raise RuntimeError("A ponte está ativa, mas não encontrou e-mails de capas aceitos (ex.: 'Monitoramento: Capa(s) de Jornais' ou 'CAPA DE JORNAIS 1 APP') para a data selecionada")
        if raw_links == 0:
            raise RuntimeError("Os e-mails foram encontrados, mas nenhum link 'Leia mais' foi localizado")
        if dated == 0:
            raise RuntimeError("Há links 'Leia mais', mas nenhum corresponde à data selecionada")
        raise RuntimeError("Nenhuma capa compatível foi classificada no Gmail para a data selecionada")

    return out, root


def download_image(url: str, dest: Path, referer: str = "", cookie_header: str = "", user_agent: str = IMAGE_UA) -> Path:
    headers = {
        "User-Agent": user_agent or IMAGE_UA,
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    }
    if referer:
        headers["Referer"] = referer
    if cookie_header:
        headers["Cookie"] = cookie_header
    with requests.get(url, timeout=(7, 18), headers=headers, stream=True, allow_redirects=True) as r:
        r.raise_for_status()
        ctype = (r.headers.get("Content-Type") or "").lower()
        if "html" in ctype:
            raise RuntimeError("O endereço retornou HTML em vez da imagem da página.")
        dest.parent.mkdir(parents=True, exist_ok=True)
        total = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(32 * 1024):
                if not chunk:
                    continue
                f.write(chunk)
                total += len(chunk)
                if total > 60 * 1024 * 1024:
                    raise RuntimeError("imagem maior que 60 MB")
    if dest.stat().st_size < 8192:
        raise RuntimeError("arquivo de imagem vazio/placeholder")
    return dest


def safe_slug(name: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "capa"
