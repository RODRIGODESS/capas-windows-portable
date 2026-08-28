from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ---------------- network.py: Windows nativo -> requests sistema -> requests direto ----------------
p = ROOT / "app/network.py"
s = p.read_text(encoding="utf-8")

s = s.replace("import re\nimport requests\n", "import re\nimport json\nimport os\nimport subprocess\nimport requests\n", 1)
if "truststore.inject_into_ssl" not in s:
    s = s.replace("import requests\n", "import requests\n\ntry:\n    import truststore\n    truststore.inject_into_ssl()\nexcept Exception:\n    pass\n", 1)

marker = '''def _valid_webapp_url(url: str) -> bool:\n    u = (url or "").strip().lower()\n    return u.startswith("https://script.google.com/macros/s/") and "/exec" in u\n\n\n'''
helper = r'''def _valid_webapp_url(url: str) -> bool:
    u = (url or "").strip().lower()
    return u.startswith("https://script.google.com/macros/s/") and "/exec" in u


def _powershell_get_text(url: str, headers: dict | None = None, timeout_sec: int = 22) -> str:
    """Fallback Windows nativo: usa WinHTTP/.NET, certificado e proxy do Windows."""
    if os.name != "nt":
        raise RuntimeError("PowerShell disponível apenas no Windows")
    env = os.environ.copy()
    env["PC_HTTP_URL"] = url
    env["PC_HTTP_UA"] = str((headers or {}).get("User-Agent") or ANDROID_FEED_UA)
    script = (
        "$ProgressPreference='SilentlyContinue';"
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;"
        "$h=@{'User-Agent'=$env:PC_HTTP_UA;'Accept'='application/json,text/plain,*/*'};"
        f"$r=Invoke-WebRequest -UseBasicParsing -Uri $env:PC_HTTP_URL -TimeoutSec {int(timeout_sec)} -Headers $h;"
        "[Console]::Out.Write($r.Content)"
    )
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    cp = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=timeout_sec + 8,
        creationflags=flags,
    )
    if cp.returncode != 0:
        err = (cp.stderr or cp.stdout or "falha no PowerShell").strip().replace("\r", " ").replace("\n", " ")
        raise RuntimeError(err[:280])
    body = (cp.stdout or "").strip()
    if not body:
        raise RuntimeError("PowerShell retornou resposta vazia")
    return body


def get_text_windows(url: str, headers: dict | None = None, connect_timeout: int = 5, read_timeout: int = 18) -> str:
    """Rede robusta para o Portable.

    1) PowerShell/Windows nativo (certificados e proxy do Windows);
    2) requests usando proxy/ambiente;
    3) requests sem proxy do ambiente.
    """
    errors = []
    if os.name == "nt":
        try:
            return _powershell_get_text(url, headers=headers, timeout_sec=max(12, read_timeout))
        except Exception as exc:
            errors.append("Windows: " + str(exc))

    for trust_env, label in ((True, "proxy/sistema"), (False, "direto")):
        try:
            with requests.Session() as session:
                session.trust_env = trust_env
                r = session.get(
                    url,
                    timeout=(connect_timeout, read_timeout),
                    headers=headers or {},
                    allow_redirects=True,
                )
                if r.status_code < 200 or r.status_code >= 300:
                    raise RuntimeError(f"HTTP {r.status_code}")
                return (r.text or "").strip()
        except Exception as exc:
            errors.append(label + ": " + str(exc))
    raise RuntimeError(" | ".join(errors[-3:]))


'''
if "def get_text_windows" not in s:
    if marker not in s:
        raise SystemExit("network helper marker não encontrado")
    s = s.replace(marker, helper, 1)

old_req = '''    session = requests.Session()\n    # requests já usa proxy do ambiente. No Windows, urllib também pode ler a\n    # configuração de proxy do sistema; trust_env precisa permanecer ativado.\n    session.trust_env = True\n    try:\n        r = session.get(\n            url,\n            timeout=(7, 25),\n            headers={"User-Agent": ANDROID_FEED_UA},\n            allow_redirects=True,\n        )\n    except requests.Timeout as exc:\n        raise RuntimeError("Ponte Gmail excedeu o tempo de resposta") from exc\n    except requests.RequestException as exc:\n        raise RuntimeError(f"Ponte Gmail: {exc}") from exc\n\n    if r.status_code < 200 or r.status_code >= 300:\n        raise RuntimeError(f"Ponte Gmail HTTP {r.status_code}")\n\n    body = (r.text or "").strip()\n'''
new_req = '''    try:\n        body = get_text_windows(\n            url,\n            headers={"User-Agent": ANDROID_FEED_UA, "Accept": "application/json,text/plain,*/*"},\n            connect_timeout=5,\n            read_timeout=18,\n        )\n    except Exception as exc:\n        raise RuntimeError(f"Ponte Gmail: {exc}") from exc\n'''
if old_req in s:
    s = s.replace(old_req, new_req, 1)

old_json = '''    try:\n        root = r.json()\n    except Exception as exc:\n        raise RuntimeError("Resposta inválida da ponte Gmail") from exc\n'''
new_json = '''    try:\n        root = json.loads(body)\n    except Exception as exc:\n        raise RuntimeError("Resposta inválida da ponte Gmail") from exc\n'''
if old_json in s:
    s = s.replace(old_json, new_json, 1)

p.write_text(s, encoding="utf-8")

# ---------------- valor_email_pdf.py: mesma pilha de rede robusta ----------------
p = ROOT / "app/valor_email_pdf.py"
s = p.read_text(encoding="utf-8")
if "import json\n" not in s:
    s = s.replace("import base64\n", "import base64\nimport json\n", 1)
s = s.replace("import requests\n\nfrom .config", "from .network import get_text_windows\n\nfrom .config", 1)
old = '''def _request_json(url: str) -> dict:\n    session = requests.Session()\n    session.trust_env = True\n    try:\n        r = session.get(\n            url,\n            timeout=(10, 120),\n            headers={"User-Agent": UA, "Accept": "application/json,text/plain,*/*"},\n            allow_redirects=True,\n        )\n    except requests.Timeout as exc:\n        raise RuntimeError("Ponte Gmail do Valor excedeu o tempo de resposta") from exc\n    except requests.RequestException as exc:\n        raise RuntimeError(f"Ponte Gmail do Valor: {exc}") from exc\n    if r.status_code < 200 or r.status_code >= 300:\n        raise RuntimeError(f"Ponte Gmail do Valor HTTP {r.status_code}")\n    body = (r.text or "").strip()\n    if body.lower().startswith(("<!doctype", "<html")):\n        raise RuntimeError("A ponte do Valor abriu HTML em vez de JSON")\n    try:\n        return r.json()\n    except Exception as exc:\n        raise RuntimeError("Resposta inválida da ponte Gmail para o Valor") from exc\n'''
new = '''def _request_json(url: str) -> dict:\n    try:\n        body = get_text_windows(\n            url,\n            headers={"User-Agent": UA, "Accept": "application/json,text/plain,*/*"},\n            connect_timeout=5,\n            read_timeout=22,\n        )\n    except Exception as exc:\n        raise RuntimeError(f"Ponte Gmail do Valor: {exc}") from exc\n    body = (body or "").strip()\n    if body.lower().startswith(("<!doctype", "<html")):\n        raise RuntimeError("A ponte do Valor abriu HTML em vez de JSON")\n    try:\n        return json.loads(body)\n    except Exception as exc:\n        raise RuntimeError("Resposta inválida da ponte Gmail para o Valor") from exc\n'''
if old in s:
    s = s.replace(old, new, 1)
else:
    if "get_text_windows(" not in s:
        raise SystemExit("valor _request_json não encontrado")
s = s.replace('UA = "PrincipaisCapas-Windows/1.2.5"', 'UA = "PrincipaisCapas-Windows/1.2.6"')
p.write_text(s, encoding="utf-8")

# ---------------- ui.py: conexão direta robusta; navegador interno como fallback ----------------
p = ROOT / "app/ui.py"
s = p.read_text(encoding="utf-8")
old = '''        # v1.1.0: o Apps Script é aberto pelo Chromium do próprio aplicativo.\n        # Isso herda proxy/certificados do Windows e elimina a diferença que\n        # fazia o requests ficar preso em "Localizando páginas no Gmail...".\n        self.gmail_feed_resolver = AppsScriptFeedResolver(self)\n        self.gmail_feed_resolver.progress.connect(self.set_status)\n        self.gmail_feed_resolver.completed.connect(\n            lambda matters, meta, g=generation: self._feed_ready((matters, meta), g)\n        )\n        self.gmail_feed_resolver.failed.connect(lambda msg, g=generation: self._feed_error(msg, g))\n        self.gmail_feed_resolver.fetch(url, self.settings.get("access_key", "PC26-8F2D4A7B-31C9E6F0-5A1D"), self.target_date())\n\n    def _feed_error(self, msg, generation):\n'''
new = '''        # v1.2.6: primeiro usa a pilha de rede Windows nativa/requests robusta.\n        # Se ainda assim falhar, cai automaticamente para o Chromium interno.\n        w = Worker(fetch_matters, url, self.target_date())\n        w.signals.finished.connect(lambda result, g=generation: self._feed_ready(result, g))\n        w.signals.error.connect(lambda msg, u=url, g=generation: self._feed_direct_error(msg, u, g))\n        self._start_worker(w)\n\n    def _feed_direct_error(self, msg, url, generation):\n        if generation != self.refresh_generation:\n            return\n        for e in self.entries:\n            if e.name in GMAIL_PAPERS:\n                e.status = "Conexão direta falhou • tentando navegador do Windows…"\n        self._refresh_list()\n        self.set_status("Gmail: tentando navegador interno após falha da conexão direta")\n        self.gmail_feed_resolver = AppsScriptFeedResolver(self)\n        self.gmail_feed_resolver.progress.connect(self.set_status)\n        self.gmail_feed_resolver.completed.connect(\n            lambda matters, meta, g=generation: self._feed_ready((matters, meta), g)\n        )\n        self.gmail_feed_resolver.failed.connect(\n            lambda browser_msg, direct_msg=str(msg), g=generation: self._feed_error(\n                f"direto: {direct_msg} | navegador: {browser_msg}", g\n            )\n        )\n        self.gmail_feed_resolver.fetch(\n            url, self.settings.get("access_key", "PC26-8F2D4A7B-31C9E6F0-5A1D"), self.target_date()\n        )\n\n    def _feed_error(self, msg, generation):\n'''
if old in s:
    s = s.replace(old, new, 1)
elif "def _feed_direct_error" not in s:
    raise SystemExit("UI feed marker não encontrado")
p.write_text(s, encoding="utf-8")

# ---------------- dependência de certificados Windows ----------------
p = ROOT / "requirements.txt"
s = p.read_text(encoding="utf-8")
if "truststore==" not in s:
    s += ("" if s.endswith("\n") else "\n") + "truststore==0.10.4\n"
p.write_text(s, encoding="utf-8")

# ---------------- versão / README ----------------
(ROOT / "version.txt").write_text("1.2.6\n", encoding="utf-8")
p = ROOT / "README.md"
s = p.read_text(encoding="utf-8")
header = '''# Principais Capas Windows Portable v1.2.6 — CONECTIVIDADE WINDOWS ROBUSTA\n\nBase: v1.2.5, preservando integralmente Valor com 3 PDFs, perfis de capa e processamento paralelo seguro.\n\n- Apps Script: tenta primeiro rede nativa do Windows (PowerShell/.NET), depois requests com proxy/sistema e conexão direta.\n- Jornais do Gmail: se a rota direta falhar, o aplicativo cai automaticamente para o Chromium interno.\n- Valor Econômico: usa a mesma pilha robusta para `valor_manifest` e `valor_pdf`, com timeouts menores e sem ficar 120 s por chamada.\n- Certificados: `truststore` integra o Python ao armazenamento de certificados do Windows.\n- Nenhuma candidata é cortada; todos os perfis e a lógica v1.2.5 permanecem.\n\n---\n\n'''
if not s.startswith("# Principais Capas Windows Portable v1.2.6"):
    s = header + s
p.write_text(s, encoding="utf-8")

print("Windows v1.2.6 conectividade robusta aplicada")
