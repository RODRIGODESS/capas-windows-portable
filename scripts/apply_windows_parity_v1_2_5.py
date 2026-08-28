from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"Marcador não encontrado: {label}")
    return text.replace(old, new, 1)

# CandidatePage: guardar PDF original do Valor.
p = ROOT / "app/models.py"
s = p.read_text(encoding="utf-8")
s = replace_once(s, '    error: str = ""\n', '    error: str = ""\n    pdf_path: Optional[Path] = None\n    source_filename: str = ""\n', "models")
p.write_text(s, encoding="utf-8")

# Renderização robusta PDF -> PNG.
p = ROOT / "requirements.txt"
s = p.read_text(encoding="utf-8")
if "PyMuPDF==" not in s:
    s += ("" if s.endswith("\n") else "\n") + "PyMuPDF==1.25.3\n"
p.write_text(s, encoding="utf-8")

# Perfis de capa (paridade Android v0.7.7.6).
p = ROOT / "app/ocr.py"
s = p.read_text(encoding="utf-8")
helper_marker = '\ndef contains_exact_estadao_masthead(text: str) -> bool:\n'
helper = '''\ndef matches_cover_profile_top(top20: str, top35: str, name: str) -> bool:\n    t20 = normalize(top20); t35 = normalize(top35); n = normalize(name)\n    if n == "O GLOBO": return "O GLOBO" in t20 or ("GLOBO" in t20 and "IRINEU MARINHO" in t35)\n    if "FOLHA" in n: return "FOLHA DE S PAULO" in t20 or "FOLHA DE SAO PAULO" in t20 or ("FOLHA" in t20 and "PAULO" in t20)\n    if "ESTADAO" in n: return contains_exact_estadao_masthead(t35)\n    if "CORREIO BRAZILIENSE" in n: return "CORREIO BRAZILIENSE" in t20 or ("CORREIO" in t20 and "BRAZILIENSE" in t20)\n    if "ESTADO DE MINAS" in n: return "ESTADO DE MINAS" in t20 or ("ESTADO" in t20 and "MINAS" in t20)\n    if "NEW YORK TIMES" in n: return is_strong_nyt_masthead(t20)\n    return matches_expected(t20, name)\n\ndef contains_exact_estadao_masthead(text: str) -> bool:\n'''
if "def matches_cover_profile_top" not in s:
    if helper_marker not in s: raise SystemExit("OCR helper")
    s = s.replace(helper_marker, helper, 1)
ad = '    ad = _contains_ad(full)\n    if ad: score -= 10 if expected20 else 35\n\n'
profile = '''    ad = _contains_ad(full)\n    if ad: score -= 10 if expected20 else 35\n\n    # v1.2.5 / Android v0.7.7.6 — perfil de capa; nunca elimina candidata.\n    profile_date = _date_matches(full, target_date)\n    profile_exact_top = matches_cover_profile_top(t20, t35, name)\n    profile_strong_top = masthead_strength >= 3 or (profile_exact_top and masthead_strength >= 2)\n    profile_medium_top = masthead_strength >= 2 or expected20 or profile_exact_top\n    profile_estadao = "ESTADAO" in normalize(name)\n    if profile_exact_top: score += 10\n    if profile_strong_top: score += 8\n    if profile_strong_top and profile_date: score += 12\n    if internal_page_marker_top and not profile_estadao and not profile_strong_top:\n        score -= 28; score = min(score, 48)\n    if not profile_medium_top and expected_full: score = min(score, 62)\n\n'''
if "v1.2.5 / Android v0.7.7.6" not in s:
    if ad not in s: raise SystemExit("OCR profile")
    s = s.replace(ad, profile, 1)
floor = '    if not expected_full: score = min(score, 55)\n'
boost = '''    if profile_exact_top and profile_strong_top and profile_date and not other and not ad and line_count >= 8:\n        score = max(score, 92)\n    elif profile_exact_top and profile_strong_top and not other and not ad:\n        score = max(score, 84)\n\n    if not expected_full: score = min(score, 55)\n'''
if "score = max(score, 92)" not in s:
    if floor not in s: raise SystemExit("OCR confidence")
    s = s.replace(floor, boost, 1)
p.write_text(s, encoding="utf-8")

# Web: restaurar Valor v1.2.2 e adicionar paralelo seguro por jornal.
p = ROOT / "app/web_resolver.py"
s = p.read_text(encoding="utf-8")
old = '''        elif name == "VALOR ECONÔMICO":\n            # v1.2.3: para o Valor, usar somente PressReader automaticamente.\n            # O FrontPages pode fornecer uma imagem já recortada na origem e esse\n            # crop nem sempre é detectável apenas por dimensão/proporção. Melhor\n            # deixar o jornal pendente do que aceitar uma capa incompleta.\n            self._sources = [\n                "https://valoreconomico.pressreader.com/valor-economico",\n            ]\n            self._slug = "valor-economico"\n'''
new = '''        elif name == "VALOR ECONÔMICO":\n            # v1.2.5: fallback web aprovado da v1.2.2.\n            self._sources = [\n                "https://www.frontpages.com/valor-economico/",\n                "https://valoreconomico.pressreader.com/valor-economico",\n            ]\n            self._slug = "valor-economico"\n'''
if "fallback web aprovado da v1.2.2" not in s:
    if old not in s: raise SystemExit("Valor sources")
    s = s.replace(old, new, 1)
marker = '\n\nclass FrontPageResolver(QObject):\n'
parallel = r'''

class ParallelCentralClippingResolver(QObject):
    """Android v0.7.7.7: até 4 jornais em paralelo, sem cortar candidatas."""
    progress = Signal(str)
    completed = Signal(object, object)
    MAX_CONCURRENT_NEWSPAPERS = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pending=[]; self._active_resolvers=[]; self._resolved=OrderedDict(); self._errors=[]; self._generation=0

    def resolve(self, matter_urls):
        self._generation += 1; g=self._generation
        self._pending=[]; self._active_resolvers=[]; self._resolved=OrderedDict(); self._errors=[]
        for name, urls in (matter_urls or {}).items():
            if name in ("VALOR ECONÔMICO", "THE WASHINGTON POST"): continue
            clean=[(u or "").strip() for u in (urls or []) if (u or "").strip()]
            if clean:
                self._pending.append((name,clean)); self._resolved.setdefault(name,[])
        self._pump(g)

    def _pump(self, g):
        if g != self._generation: return
        while self._pending and len(self._active_resolvers) < self.MAX_CONCURRENT_NEWSPAPERS:
            name, urls = self._pending.pop(0)
            r = CentralClippingBatchResolver(self); self._active_resolvers.append(r)
            r.progress.connect(self.progress.emit)
            r.completed.connect(lambda covers, errors, rr=r, n=name, gen=g: self._one_done(rr,n,covers,errors,gen))
            r.resolve({name: urls})
        if not self._pending and not self._active_resolvers:
            out=OrderedDict()
            for name,items in self._resolved.items(): out[name]=sorted(items,key=lambda x:int(x.get("page_number",999)))
            self.completed.emit(dict(out), list(self._errors))

    def _one_done(self, resolver, name, covers, errors, g):
        if g != self._generation: return
        try: self._active_resolvers.remove(resolver)
        except ValueError: pass
        self._resolved[name]=list((covers or {}).get(name,[]) or [])
        self._errors.extend(list(errors or [])); resolver.deleteLater()
        QTimer.singleShot(0, lambda gen=g: self._pump(gen))


class FrontPageResolver(QObject):
'''
if "class ParallelCentralClippingResolver" not in s:
    if marker not in s: raise SystemExit("Parallel marker")
    s=s.replace(marker,parallel,1)
p.write_text(s,encoding="utf-8")

# UI: usar resolver paralelo + Valor Gmail 3 PDFs + fallback v1.2.2.
p = ROOT / "app/ui.py"
s = p.read_text(encoding="utf-8")
s=s.replace('from .web_resolver import Resolver, CentralClippingBatchResolver, AppsScriptFeedResolver, ANDROID_FRONT_UA\n', 'from .web_resolver import Resolver, CentralClippingBatchResolver, ParallelCentralClippingResolver, AppsScriptFeedResolver, ANDROID_FRONT_UA\nfrom .valor_email_pdf import load_valor_candidates\n', 1)
s=s.replace('self.gmail_batch_resolver = CentralClippingBatchResolver(self)', 'self.gmail_batch_resolver = ParallelCentralClippingResolver(self)', 1)
start=s.find('    # ---------------- Valor / Washington Post ----------------\n    def _start_web_branch')
end=s.find('    def _web_resolved(',start)
if start < 0 or end < 0: raise SystemExit("UI Valor branch")
branch=r'''    # ---------------- Valor / Washington Post ----------------
    def _start_web_branch(self, generation):
        if generation != self.refresh_generation: return
        web_entries=[]
        for e in self.entries:
            if e.name == "VALOR ECONÔMICO":
                if self.target_date().weekday() >= 5: e.status="Sem edição regular no fim de semana"
                else: e.status="Valor: procurando 3 PDFs no Gmail…"; web_entries.append(e)
            elif e.name == "THE WASHINGTON POST":
                e.status="Buscando a capa exibida atualmente no link…"; web_entries.append(e)
        self._refresh_list()
        if not web_entries: self._branch_done(generation); return
        pending={"n":len(web_entries)}
        def one_done():
            if generation != self.refresh_generation: return
            pending["n"]-=1
            if pending["n"] <= 0: self._branch_done(generation)
        for e in web_entries:
            if e.name == "VALOR ECONÔMICO":
                w=Worker(load_valor_candidates,self.settings.get("apps_script_url",""),self.target_date())
                w.signals.finished.connect(lambda cand,en=e,g=generation,d=one_done:self._valor_email_ready(en,cand,g,d))
                w.signals.error.connect(lambda msg,en=e,g=generation,d=one_done:self._valor_email_error(en,msg,g,d))
                self._start_worker(w)
            else: self._start_single_web_resolver(e,generation,one_done)

    def _valor_email_ready(self,e,candidates,generation,one_done):
        if generation != self.refresh_generation: return
        candidates=list(candidates or [])
        indexes=[i for i,c in enumerate(candidates) if c.page_number==1 and c.available and c.path and c.path.exists()]
        if indexes:
            e.candidates=candidates; idx=indexes[0]
            e.chosen_index=idx; e.review_index=idx; e.automatic_index=idx
            available=sum(1 for c in candidates if c.available and c.path and c.path.exists()); total=len(candidates)
            e.automatic_status=(f"Gmail • {available}/{total} PDF(s) do Valor no aplicativo • {total} página(s) em REVISAR CAPA • "
                                "Página 1 selecionada • cópia em Downloads/Principais Capas/Valor Economico")
            e.status=e.automatic_status; self._refresh_list()
            if self.current_entry is e: self._show_entry()
            one_done(); return
        e.status="Valor: Página 1 não veio do Gmail • usando fallback web v1.2.2…"; self._refresh_list()
        self._start_single_web_resolver(e,generation,one_done)

    def _valor_email_error(self,e,msg,generation,one_done):
        if generation != self.refresh_generation: return
        e.status=f"Valor: Gmail indisponível ({msg}) • usando fallback web v1.2.2…"; self._refresh_list()
        self._start_single_web_resolver(e,generation,one_done)

    def _start_single_web_resolver(self,e,generation,one_done,pressreader_only=False):
        resolver=Resolver(self); resolver.progress.connect(self.set_status); self.web_resolvers.append(resolver)
        cb=lambda url,err,en=e,r=resolver,g=generation:self._web_resolved(en,r,url,err,g,one_done)
        if pressreader_only: resolver.resolve_pressreader_only(cb)
        else: resolver.resolve_frontpages(e.name,cb)

'''
s=s[:start]+branch+s[end:]
s=s.replace('lambda c, en=e, g=generation: self._web_candidate_ready(en, c, g, one_done)', 'lambda c, en=e, r=resolver, g=generation: self._web_candidate_ready(en, r, c, g, one_done)', 1)
s=s.replace('    def _web_candidate_ready(self, e, candidate, generation, one_done):\n', '    def _web_candidate_ready(self, e, resolver, candidate, generation, one_done):\n', 1)
mark='''        # Segurança extra igual ao Android: nunca aceitar Washington Post SPORTS.\n'''
inject='''        # v1.2.5: validação exclusiva do Valor/FrontPages da base v1.2.2.\n        if e.name == "VALOR ECONÔMICO" and "frontpages.com" in candidate.source_url.lower():\n            try:\n                with Image.open(candidate.path) as im: w,h=im.size\n                complete=w>=700 and h>=950 and h/max(1,w)>=1.34\n            except Exception: complete=False\n            if not complete:\n                try: candidate.path.unlink(missing_ok=True)\n                except Exception: pass\n                e.status="Valor: FrontPages retornou capa recortada • tentando PressReader…"; self._refresh_list()\n                self._start_single_web_resolver(e,generation,one_done,pressreader_only=True); return\n\n        # Segurança extra igual ao Android: nunca aceitar Washington Post SPORTS.\n'''
if "validação exclusiva do Valor/FrontPages" not in s:
    if mark not in s: raise SystemExit("UI Valor validation")
    s=s.replace(mark,inject,1)
old_err='''    def _web_candidate_error(self, e, resolver, msg, generation, one_done):\n        if generation != self.refresh_generation:\n            return\n        e.status = f"Falha ao baixar capa: {msg}"\n        self._refresh_list()\n        one_done()\n'''
new_err='''    def _web_candidate_error(self, e, resolver, msg, generation, one_done):\n        if generation != self.refresh_generation:\n            return\n        if e.name == "VALOR ECONÔMICO" and "frontpages.com" in (resolver.last_referer or "").lower():\n            e.status=f"Valor: FrontPages falhou ({msg}) • tentando PressReader…"; self._refresh_list()\n            self._start_single_web_resolver(e,generation,one_done,pressreader_only=True); return\n        e.status = f"Falha ao baixar capa: {msg}"\n        self._refresh_list(); one_done()\n'''
if "Valor: FrontPages falhou" not in s:
    if old_err not in s: raise SystemExit("UI web error")
    s=s.replace(old_err,new_err,1)
p.write_text(s,encoding="utf-8")

# Versão e documentação.
(ROOT/"version.txt").write_text("1.2.5\n",encoding="utf-8")
p=ROOT/"README.md"; s=p.read_text(encoding="utf-8")
header='''# Principais Capas Windows Portable v1.2.5 — PARIDADE ANDROID 0.7.7.7\n\nBase funcional: Windows v1.2.2, preservando interface e PDF.\n\n- Valor Econômico prioriza `valor_manifest`/`valor_pdf` do Gmail.\n- Páginas 1, 2 e 3 ficam no aplicativo e em `Downloads/Principais Capas/Valor Economico`; Página 1 é a capa automática.\n- Se Página 1 falhar, fallback v1.2.2: FrontPages → validação de capa completa (razão >= 1,34) → PressReader.\n- Perfis de capa por jornal reduzem falsos positivos sem eliminar candidatas.\n- Até 4 jornais do Gmail são resolvidos em paralelo; todas as candidatas e sua ordem são preservadas.\n- Revisão manual, inserção manual, PDF, Abrir PDF/Abrir Pasta e Releases permanecem.\n\n---\n\n'''
if not s.startswith("# Principais Capas Windows Portable v1.2.5"): s=header+s
p.write_text(s,encoding="utf-8")
print("Windows v1.2.5 aplicado")
