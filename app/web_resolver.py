from __future__ import annotations

import json
import itertools
from collections import OrderedDict
from typing import Callable, Optional

from PySide6.QtCore import QObject, QTimer, QUrl, Signal, QRect
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineUrlRequestInterceptor,
)
from PySide6.QtWebEngineWidgets import QWebEngineView


ANDROID_GMAIL_UA = (
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124 Mobile Safari/537.36"
)
ANDROID_FRONT_UA = (
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
)


def _cleanup(value: str) -> str:
    return (value or "").replace("\\u0026", "&").replace("&amp;", "&").replace("\\/", "/").strip()


def _is_original(url: str) -> bool:
    u = (url or "").lower()
    return (
        "/original_page/" in u
        or "static.resources/original_page/" in u
        or "static.resources%2foriginal_page%2f" in u
    )


# Transcrição funcional do probe de CentralClippingWebResolver.java (Android v0.7.5.9).
# A única diferença é que, no Qt, navegação e requests são capturados por CapturePage
# e RequestInterceptor em vez da @JavascriptInterface do WebView.
ORIGINAL_PROBE_JS = r"""
(function(){
 function norm(s){try{return (s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase()}catch(e){return (s||'').toUpperCase()}}
 function clean(u){if(!u)return '';try{u=String(u).replace(/\\\//g,'/').replace(/&amp;/g,'&');return new URL(u,document.baseURI).href}catch(e){return String(u||'')}}
 function isOrig(u){u=String(u||'').toLowerCase();return u.indexOf('/original_page/')>=0||u.indexOf('static.resources/original_page/')>=0||u.indexOf('static.resources%2foriginal_page%2f')>=0}
 function direct(v){v=clean(v);return isOrig(v)?v:''}
 try{var pe=performance.getEntriesByType('resource')||[];for(var pi=0;pi<pe.length;pi++){var pu=direct(pe[pi].name);if(pu)return pu}}catch(e){}
 try{var nodes=[].slice.call(document.querySelectorAll('*'));for(var ni=0;ni<nodes.length&&ni<9000;ni++){var n=nodes[ni];if(!n||!n.attributes)continue;for(var ai=0;ai<n.attributes.length;ai++){var du=direct(n.attributes[ai].value);if(du)return du}}}catch(e){}
 try{var html=document.documentElement?document.documentElement.innerHTML:'';var hm=html.match(/https?:\/\/[^'\"<>\s]+original_page[^'\"<>\s]*/i);if(hm&&hm[0]){var hu=direct(hm[0]);if(hu)return hu}}catch(e){}
 var all=[].slice.call(document.querySelectorAll('a,button,[role=button],input[type=button],input[type=submit],[onclick],[data-url],[data-href]'));
 var el=null;
 for(var i=0;i<all.length;i++){var t=norm(all[i].innerText||all[i].textContent||all[i].value||all[i].getAttribute('aria-label')||all[i].getAttribute('title')||'').trim();if(t==='VER PAGINA'||t.indexOf('VER PAGINA')===0){el=all[i];break}}
 if(!el){var every=[].slice.call(document.querySelectorAll('span,div,p,strong'));for(var j=0;j<every.length&&j<7000;j++){var tt=norm(every[j].innerText||every[j].textContent||'').trim();if(tt==='VER PAGINA'||tt.indexOf('VER PAGINA')===0){el=every[j].closest('a,button,[role=button],[onclick],[data-url],[data-href]');if(!el&&every[j].querySelector)el=every[j].querySelector('a,button,[role=button]');if(el)break}}}
 if(!el)return '';
 var attrs=['href','data-href','data-url','data-original','data-image','data-page','src'];
 var cur=el;
 for(var up=0;up<4&&cur;up++,cur=cur.parentElement){for(var k=0;k<attrs.length;k++){var u=cur.getAttribute?cur.getAttribute(attrs[k]):'';u=clean(u);if(u&&u.indexOf('javascript:')!==0){if(isOrig(u))return u;if(/^https?:/i.test(u))return u}}}
 var child=el.querySelector?el.querySelector('a[href]'):null;if(child){var cu=clean(child.getAttribute('href'));if(cu)return cu}
 var oc=el.getAttribute?el.getAttribute('onclick')||'':'';var mm=oc.match(/https?:\/\/[^'\"\s)]+/i);if(mm&&mm[0])return clean(mm[0]);
 try{el.click()}catch(e){}
 return '__CLICKED__';
})()
"""


# Exatamente a lógica "capa que o link está exibindo agora" do Android v0.7.5.9.
CURRENT_WEBP_JS = r"""
(function(slug){
 function pick(u){try{u=String(u||'');var l=u.toLowerCase();if(l.indexOf('/g/')<0||l.indexOf('/'+slug+'-')<0||l.indexOf('.webp')<0)return '';if(slug==='the-washington-post'&&l.indexOf('sports')>=0)return '';var p=l.indexOf('/g/'),e=l.indexOf('.webp',p);if(p<0||e<0)return '';var x=u.substring(p,e+5);if(x.indexOf('/g/')===0)x='https://www.frontpages.com'+x;return x}catch(e){return ''}}
 try{var rr=performance.getEntriesByType('resource')||[];for(var i=0;i<rr.length;i++){var v=pick(rr[i].name);if(v)return v}}catch(e){}
 try{var imgs=document.images||[];for(var j=0;j<imgs.length;j++){var im=imgs[j],v=pick(im.currentSrc||im.src);if(v)return v;var aa=['src','data-src','data-lazy-src','data-original','data-image','data-url','data-full'];for(var a=0;a<aa.length;a++){v=pick(im.getAttribute(aa[a]));if(v)return v}var ss=(im.getAttribute('srcset')||im.getAttribute('data-srcset')||'').split(',');for(var k=0;k<ss.length;k++){v=pick(ss[k].trim().split(/\s+/)[0]);if(v)return v}}}catch(e){}
 try{var els=document.querySelectorAll('source,a,[data-src],[data-lazy-src],[data-original],[data-image],[data-url],[data-full]');for(var z=0;z<els.length;z++){var el=els[z];var aa=['src','href','srcset','data-src','data-lazy-src','data-original','data-image','data-url','data-full'];for(var q=0;q<aa.length;q++){var raw=el.getAttribute(aa[q])||'';var parts=raw.split(',');for(var b=0;b<parts.length;b++){var v=pick(parts[b].trim().split(/\s+/)[0]);if(v)return v}}}}catch(e){}
 try{var html=document.documentElement?document.documentElement.innerHTML:'';var low=html.toLowerCase(),key='/'+slug+'-',pos=low.indexOf(key);while(pos>=0){var gp=low.lastIndexOf('/g/',pos),we=low.indexOf('.webp',pos);if(gp>=0&&we>pos){var x=html.substring(gp,we+5).replace(/&amp;/g,'&').replace(/\\\//g,'/');if(x.indexOf('/g/')===0)x='https://www.frontpages.com'+x;if(!(slug==='the-washington-post'&&x.toLowerCase().indexOf('sports')>=0))return x}pos=low.indexOf(key,pos+key.length)}}catch(e){}
 return '';
})(%SLUG%)
"""

STANDARD_IMAGE_JS = r"""
(function(expected){
 function norm(s){try{return (s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase().replace(/[^A-Z0-9]+/g,' ').trim()}catch(e){return (s||'').toUpperCase()}}
 var imgs=Array.prototype.slice.call(document.images||[]),best=null;
 for(var i=0;i<imgs.length;i++){
   var im=imgs[i],w=im.naturalWidth||0,h=im.naturalHeight||0;if(w<300||h<450)continue;
   var raw=(im.currentSrc||im.src||'');var low=raw.toLowerCase();
   if(expected.indexOf('WASHINGTON POST')>=0&&low.indexOf('sports')>=0)continue;
   var ar=h/Math.max(1,w);if(ar<1.10||ar>2.20)continue;
   var a=im.closest?im.closest('a'):null,par=im.parentElement;
   var info=norm((im.alt||'')+' '+(im.title||'')+' '+(im.getAttribute('data-title')||'')+' '+(im.getAttribute('data-caption')||'')+' '+(a?(a.title||''):'')+' '+(par?(par.innerText||'').slice(0,450):''));
   var y=0;try{y=im.getBoundingClientRect().top+(window.scrollY||0)}catch(e){}
   var score=Math.min(w*h,12000000)+Math.max(0,3500-Math.min(3500,y))*3500;
   if(expected.indexOf('WASHINGTON POST')>=0&&info.indexOf('WASHINGTON POST')>=0)score+=25000000;
   if(expected.indexOf('VALOR ECONOMICO')>=0&&info.indexOf('VALOR')>=0)score+=25000000;
   if(low.indexOf('logo')>=0||low.indexOf('icon')>=0||low.indexOf('avatar')>=0)score-=15000000;
   if(!best||score>best.score)best={url:raw,w:w,h:h,score:score,info:info};
 }
 return best?JSON.stringify(best):'';
})(%EXPECTED%)
"""


class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    captured = Signal(str)

    def interceptRequest(self, info):  # noqa: N802
        try:
            u = info.requestUrl().toString()
            if _is_original(u):
                self.captured.emit(u)
        except Exception:
            pass


class CapturePage(QWebEnginePage):
    captured = Signal(str)

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):  # noqa: N802
        s = url.toString()
        if _is_original(s):
            self.captured.emit(s)
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)

    def createWindow(self, _type):  # noqa: N802
        # Android usa supportMultipleWindows=false. O popup "Ver página" é
        # reaproveitado na mesma WebView; no Qt fazemos a mesma coisa.
        return self


class _AttachedBrowser(QObject):
    """Página Chromium realmente anexada a um QWebEngineView fora da tela.

    A v1.0.1 usava apenas QWebEnginePage sem uma View. Isso muda o comportamento
    de lazy-load, window.open e recursos renderizados. O Android mantém a WebView
    anexada à Activity (2x2 px); esta classe reproduz esse detalhe no Windows.
    """

    _ids = itertools.count(1)

    def __init__(self, owner: QObject, user_agent: str):
        super().__init__(owner)
        self.owner = owner
        self.profile = QWebEngineProfile(f"PrincipaisCapas-{next(self._ids)}", self)
        self.profile.setHttpUserAgent(user_agent)
        self.interceptor = RequestInterceptor(self)
        self.profile.setUrlRequestInterceptor(self.interceptor)
        self.view: Optional[QWebEngineView] = None
        self.page: Optional[CapturePage] = None

    def new_page(self, captured_callback: Callable[[str], None]) -> CapturePage:
        self.destroy_page()
        parent_widget = self.owner if isinstance(self.owner, QWebEngineView) else None
        # Normalmente owner é MainWindow/QObject. QWebEngineView aceita QWidget;
        # se owner não for QWidget, fica top-level, porém fora da tela.
        try:
            from PySide6.QtWidgets import QWidget
            if isinstance(self.owner, QWidget):
                parent_widget = self.owner
        except Exception:
            parent_widget = None
        self.view = QWebEngineView(parent_widget)
        self.view.setGeometry(QRect(-5000, 0, 1200, 1600))
        self.page = CapturePage(self.profile, self.view)
        self.page.captured.connect(captured_callback)
        self.view.setPage(self.page)

        settings = self.page.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        # Fora da área visível, mas anexada/ativa como a WebView do Android.
        self.view.show()
        return self.page

    def destroy_page(self):
        if self.page:
            try:
                self.page.triggerAction(QWebEnginePage.WebAction.Stop)
            except Exception:
                try:
                    self.page.triggerAction(QWebEnginePage.Stop)
                except Exception:
                    pass
        if self.view:
            try:
                self.view.hide()
                self.view.setPage(QWebEnginePage(self.view))
                self.view.deleteLater()
            except Exception:
                pass
        self.page = None
        self.view = None


class CentralClippingBatchResolver(QObject):
    """Port direto de CentralClippingWebResolver.java do Android v0.7.5.9."""

    progress = Signal(str)
    completed = Signal(object, object)  # dict[str,list[str]], list[str]

    MAX_MATTERS_PER_PAPER = 5
    MAX_ORIGINALS_PER_PAPER = 5
    JOB_TIMEOUT_MS = 12000

    def __init__(self, parent=None):
        super().__init__(parent)
        self.browser = _AttachedBrowser(parent or self, ANDROID_GMAIL_UA)
        self.browser.interceptor.captured.connect(self._intercepted)
        self.jobs: list[tuple[str, str]] = []
        self.resolved: OrderedDict[str, list[str]] = OrderedDict()
        self.errors: list[str] = []
        self.job_index = 0
        self.current_job: Optional[tuple[str, str]] = None
        self.generation = 0
        self.probe_count = 0
        self.page: Optional[CapturePage] = None

    def resolve(self, matter_urls: dict[str, list[str]]):
        self.jobs.clear(); self.resolved.clear(); self.errors.clear(); self.job_index = 0
        self.current_job = None; self.generation += 1
        for name, urls in (matter_urls or {}).items():
            if name in ("VALOR ECONÔMICO", "THE WASHINGTON POST"):
                continue
            n = 0
            for u in (urls or []):
                u = (u or "").strip()
                if not u:
                    continue
                self.jobs.append((name, u))
                n += 1
                if n >= self.MAX_MATTERS_PER_PAPER:
                    break
        self._start_next_job()

    def _start_next_job(self):
        self.browser.destroy_page()
        while self.job_index < len(self.jobs):
            job = self.jobs[self.job_index]
            self.job_index += 1
            name, url = job
            if len(self.resolved.get(name, [])) >= self.MAX_ORIGINALS_PER_PAPER:
                continue
            self.current_job = job
            self.probe_count = 0
            self.generation += 1
            g = self.generation
            self.progress.emit(f"{name}: abrindo Leia mais → Ver página…")
            self.page = self.browser.new_page(lambda u, gen=g: self._captured(u, gen))
            self.page.loadFinished.connect(lambda ok, gen=g: self._after_load(ok, gen))
            self.page.load(QUrl(url))
            QTimer.singleShot(self.JOB_TIMEOUT_MS, lambda gen=g, nm=name: self._timeout(gen, nm))
            return
        self._finish()

    def _after_load(self, ok: bool, generation: int):
        if not self._active(generation):
            return
        if not ok:
            # Android continua até o timeout/probe porque redirects intermediários
            # podem marcar loadFinished=false. Tentamos o DOM antes de desistir.
            QTimer.singleShot(250, lambda gen=generation: self._probe(gen))
            return
        QTimer.singleShot(250, lambda gen=generation: self._probe(gen))

    def _probe(self, generation: int):
        if not self._active(generation) or not self.page:
            return
        self.probe_count += 1
        self.page.runJavaScript(ORIGINAL_PROBE_JS, lambda r, gen=generation: self._probe_result(r, gen))

    def _probe_result(self, result, generation: int):
        if not self._active(generation):
            return
        text = _cleanup(str(result or ""))
        if _is_original(text):
            self._success(text, generation)
            return
        if text.startswith(("http://", "https://")):
            if self.page:
                self.page.load(QUrl(text))
            QTimer.singleShot(450, lambda gen=generation: self._probe(gen))
            return
        if self.probe_count < 20:
            QTimer.singleShot(450, lambda gen=generation: self._probe(gen))

    def _intercepted(self, url: str):
        if self.current_job and _is_original(url):
            self._success(url, self.generation)

    def _captured(self, url: str, generation: int):
        if self._active(generation) and _is_original(url):
            self._success(url, generation)

    def _success(self, url: str, generation: int):
        if not self._active(generation) or not self.current_job:
            return
        name, _ = self.current_job
        clean = _cleanup(url)
        if not _is_original(clean):
            return
        arr = self.resolved.setdefault(name, [])
        if clean not in arr and len(arr) < self.MAX_ORIGINALS_PER_PAPER:
            arr.append(clean)
        self.generation += 1
        self.current_job = None
        self._start_next_job()

    def _timeout(self, generation: int, name: str):
        if not self._active(generation):
            return
        self.errors.append(f"{name}: Ver página não localizado no link exato")
        self.generation += 1
        self.current_job = None
        self._start_next_job()

    def _active(self, generation: int) -> bool:
        return self.current_job is not None and generation == self.generation

    def _finish(self):
        self.browser.destroy_page()
        self.completed.emit(dict(self.resolved), list(self.errors))


class FrontPageResolver(QObject):
    """Port do FrontPageBrowserResolver.java do Android v0.7.5.9."""

    progress = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.browser = _AttachedBrowser(parent or self, ANDROID_FRONT_UA)
        self.page: Optional[CapturePage] = None
        self.done_cb = None
        self._generation = 0
        self._finished = True
        self._scan_count = 0
        self._name = ""
        self._slug = ""
        self._sources: list[str] = []
        self._source_index = -1
        self.last_referer = ""

    def resolve(self, newspaper_name: str, callback: Callable[[str | None, str | None], None]):
        name = (newspaper_name or "").upper().strip()
        if name == "THE WASHINGTON POST":
            self._sources = ["https://www.frontpages.com/the-washington-post/"]
            self._slug = "the-washington-post"
        elif name == "VALOR ECONÔMICO":
            self._sources = [
                "https://www.frontpages.com/valor-economico/",
                "https://valoreconomico.pressreader.com/valor-economico",
            ]
            self._slug = "valor-economico"
        else:
            callback(None, "resolver web não se aplica a este jornal")
            return
        self._name = name
        self.done_cb = callback
        self._source_index = -1
        self._start_next_source()

    # Nome mantido para compatibilidade com a UI da v1.0.1.
    def resolve_frontpages(self, newspaper_name: str, callback):
        return self.resolve(newspaper_name, callback)

    def _start_next_source(self):
        self.browser.destroy_page()
        self._source_index += 1
        if self._source_index >= len(self._sources):
            cb = self.done_cb; self.done_cb = None; self._finished = True
            if cb:
                cb(None, "capa correta não confirmada (timeout/capa não localizada)")
            return
        self._generation += 1
        g = self._generation
        self._finished = False
        self._scan_count = 0
        source = self._sources[self._source_index]
        self.last_referer = source
        self.progress.emit("Abrindo FrontPages…" if "frontpages.com" in source else "Tentando PressReader…")
        self.page = self.browser.new_page(lambda _u, _g=g: None)
        self.page.loadFinished.connect(lambda ok, gen=g: self._after_load(ok, gen))
        self.page.load(QUrl(source))
        QTimer.singleShot(18000, lambda gen=g: self._source_failed("timeout do navegador interno", gen))

    def _after_load(self, ok: bool, generation: int):
        if not self._active(generation):
            return
        if not ok:
            # Como no Android, ainda damos tempo ao DOM/lazy-load antes do fallback.
            QTimer.singleShot(1200, lambda gen=generation: self._scan(gen))
            return
        QTimer.singleShot(1200, lambda gen=generation: self._scan(gen))

    def _scan(self, generation: int):
        if not self._active(generation) or not self.page:
            return
        self._scan_count += 1
        source = self._sources[self._source_index]
        if "frontpages.com" in source:
            js = CURRENT_WEBP_JS.replace("%SLUG%", json.dumps(self._slug))
            self.page.runJavaScript(js, lambda r, gen=generation: self._direct_result(r, gen))
        else:
            self._scan_standard(generation)

    def _direct_result(self, result, generation: int):
        if not self._active(generation):
            return
        url = _cleanup(str(result or ""))
        low = url.lower()
        expected = (
            url.startswith("https://www.frontpages.com/g/")
            and f"/{self._slug}-" in low
            and ".webp" in low
            and not (self._slug == "the-washington-post" and "sports" in low)
        )
        if expected:
            self._success(url, generation)
            return
        if self._scan_count < 4:
            QTimer.singleShot(900, lambda gen=generation: self._scan(gen))
            return
        self._scan_standard(generation)

    def _scan_standard(self, generation: int):
        if not self._active(generation) or not self.page:
            return
        expected = "WASHINGTON POST" if self._name == "THE WASHINGTON POST" else "VALOR ECONOMICO"
        js = STANDARD_IMAGE_JS.replace("%EXPECTED%", json.dumps(expected))
        self.page.runJavaScript(js, lambda r, gen=generation: self._standard_result(r, gen))

    def _standard_result(self, result, generation: int):
        if not self._active(generation):
            return
        raw = str(result or "").strip()
        if raw:
            try:
                data = json.loads(raw)
                url = _cleanup(str(data.get("url") or ""))
                w = int(data.get("w") or 0); h = int(data.get("h") or 0)
                low = url.lower()
                if (
                    url.startswith(("http://", "https://"))
                    and w >= 300 and h >= 450
                    and h / max(1, w) >= 1.10
                    and not (self._name == "THE WASHINGTON POST" and "sports" in low)
                ):
                    self._success(url, generation)
                    return
            except Exception:
                pass
        self._source_failed("capa principal não localizada na página", generation)

    def _source_failed(self, _msg: str, generation: int):
        if not self._active(generation):
            return
        self._finished = True
        self._generation += 1
        self._start_next_source()

    def _active(self, generation: int) -> bool:
        return not self._finished and generation == self._generation

    def _success(self, url: str, generation: int):
        if not self._active(generation):
            return
        self._finished = True
        self._generation += 1
        self.browser.destroy_page()
        cb = self.done_cb; self.done_cb = None
        if cb:
            cb(_cleanup(url), None)


# Compatibilidade para qualquer import antigo dentro do projeto.
Resolver = FrontPageResolver
