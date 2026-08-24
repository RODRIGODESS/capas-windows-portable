from __future__ import annotations

import json
from typing import Callable, Optional

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineUrlRequestInterceptor,
)


# Mesmo princípio do Android v0.7.5.9:
# Leia mais -> Ver página -> URL original_page. A busca é deliberadamente ampla
# porque o Central Clipping muda pequenos detalhes do HTML entre boletins.
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


# Mesmo motor "capa atual do link" usado no Android para Valor e Washington Post.
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


# Fallback do Android quando o caminho /g/...webp ainda não foi revelado. Em vez
# de depender da data selecionada, procura a maior imagem vertical da página.
STANDARD_IMAGE_JS = r"""
(function(expected){
 function norm(s){try{return (s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase().replace(/[^A-Z0-9]+/g,' ').trim()}catch(e){return (s||'').toUpperCase()}}
 var imgs=Array.prototype.slice.call(document.images||[]),best=null;
 for(var i=0;i<imgs.length;i++){
   var im=imgs[i],w=im.naturalWidth||0,h=im.naturalHeight||0;if(w<300||h<450)continue;
   var raw=(im.currentSrc||im.src||'');var low=raw.toLowerCase();
   if(expected.indexOf('WASHINGTON POST')>=0&&low.indexOf('sports')>=0)continue;
   var ar=h/Math.max(1,w);if(ar<1.10||ar>2.30)continue;
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


def _is_original(url: str) -> bool:
    u = (url or "").lower()
    return "/original_page/" in u or "static.resources/original_page/" in u or "static.resources%2foriginal_page%2f" in u


class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    captured = Signal(str)

    def interceptRequest(self, info):  # noqa: N802 (Qt API)
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
        # window.open do botão "Ver página" permanece na mesma página oculta,
        # equivalente ao WebView novo usado no Android.
        return self


class Resolver(QObject):
    """Um resolver independente por ramo.

    IMPORTANTE: cada instância tem geração própria. Isso impede que o timeout de
    uma candidata anterior mate a candidata seguinte — problema da v1.0.0.
    """

    progress = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile = QWebEngineProfile(self)
        self.profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
        )
        self.interceptor = RequestInterceptor(self)
        self.interceptor.captured.connect(self._intercepted)
        self.profile.setUrlRequestInterceptor(self.interceptor)
        self.page: Optional[CapturePage] = None
        self.done_cb = None
        self._finished = True
        self._generation = 0
        self._probe_count = 0
        self._mode = ""
        self._front_name = ""
        self._front_slug = ""
        self._front_sources: list[str] = []
        self._front_source_index = -1
        self.last_referer = ""

    def _new_page(self, generation: int):
        if self.page:
            try:
                self.page.triggerAction(QWebEnginePage.Stop)
            except Exception:
                pass
            try:
                self.page.deleteLater()
            except Exception:
                pass
        self.page = CapturePage(self.profile, self)
        self.page.captured.connect(lambda u, g=generation: self._success(u, g))
        return self.page

    # ---------------- Gmail / Central Clipping ----------------
    def resolve_original(self, matter_url: str, callback: Callable[[str | None, str | None], None]):
        self._generation += 1
        g = self._generation
        self.done_cb = callback
        self._finished = False
        self._mode = "original"
        self._probe_count = 0
        self.last_referer = matter_url
        page = self._new_page(g)
        self.progress.emit("Abrindo Leia mais → Ver página…")
        page.loadFinished.connect(lambda ok, gen=g: self._after_load_original(ok, gen))
        page.load(QUrl(matter_url))
        QTimer.singleShot(12000, lambda gen=g: self._fail("Ver página não localizado no link exato", gen))

    def _after_load_original(self, ok: bool, generation: int):
        if not self._active(generation):
            return
        if not ok:
            self._fail("falha ao abrir o link do clipping", generation)
            return
        QTimer.singleShot(250, lambda gen=generation: self._probe_original(gen))

    def _probe_original(self, generation: int):
        if not self._active(generation) or not self.page:
            return
        self._probe_count += 1
        self.page.runJavaScript(
            ORIGINAL_PROBE_JS,
            lambda result, gen=generation: self._original_probe_result(result, gen),
        )

    def _original_probe_result(self, result, generation: int):
        if not self._active(generation):
            return
        text = str(result or "").replace("\\/", "/").replace("&amp;", "&").strip()
        if _is_original(text):
            self._success(text, generation)
            return
        if text.startswith("http://") or text.startswith("https://"):
            # O botão pode apontar para uma página intermediária que então abre
            # original_page. Navegamos nela e continuamos sondando.
            if self.page:
                self.page.load(QUrl(text))
            QTimer.singleShot(450, lambda gen=generation: self._probe_original(gen))
            return
        if self._probe_count < 20:
            QTimer.singleShot(450, lambda gen=generation: self._probe_original(gen))

    def _intercepted(self, url: str):
        if self._mode == "original" and not self._finished and _is_original(url):
            self._success(url, self._generation)

    # ---------------- Valor / Washington Post ----------------
    def resolve_frontpages(self, newspaper_name: str, callback: Callable[[str | None, str | None], None]):
        name = (newspaper_name or "").upper().strip()
        if name == "THE WASHINGTON POST":
            sources = ["https://www.frontpages.com/the-washington-post/"]
            slug = "the-washington-post"
        elif name == "VALOR ECONÔMICO":
            sources = [
                "https://www.frontpages.com/valor-economico/",
                "https://valoreconomico.pressreader.com/valor-economico",
            ]
            slug = "valor-economico"
        else:
            callback(None, "resolver web não se aplica a este jornal")
            return

        self.done_cb = callback
        self._front_name = name
        self._front_slug = slug
        self._front_sources = sources
        self._front_source_index = -1
        self._start_next_front_source()

    def _start_next_front_source(self):
        self._front_source_index += 1
        if self._front_source_index >= len(self._front_sources):
            cb = self.done_cb
            self.done_cb = None
            self._finished = True
            if cb:
                cb(None, "capa correta não confirmada (timeout/capa não localizada)")
            return

        self._generation += 1
        g = self._generation
        self._finished = False
        self._mode = "front"
        self._probe_count = 0
        source = self._front_sources[self._front_source_index]
        self.last_referer = source
        page = self._new_page(g)
        self.progress.emit(
            ("Abrindo FrontPages…" if "frontpages.com" in source else "Tentando PressReader…")
        )
        page.loadFinished.connect(lambda ok, gen=g: self._after_load_front(ok, gen))
        page.load(QUrl(source))
        QTimer.singleShot(18000, lambda gen=g: self._front_source_failed("timeout do navegador interno", gen))

    def _after_load_front(self, ok: bool, generation: int):
        if not self._active(generation):
            return
        if not ok:
            self._front_source_failed("falha ao abrir a fonte", generation)
            return
        # Android espera o lazy-load da capa após onPageFinished.
        QTimer.singleShot(1200, lambda gen=generation: self._probe_front(gen))

    def _probe_front(self, generation: int):
        if not self._active(generation) or not self.page:
            return
        self._probe_count += 1
        source = self._front_sources[self._front_source_index]
        if "frontpages.com" in source:
            js = CURRENT_WEBP_JS.replace("%SLUG%", json.dumps(self._front_slug))
            self.page.runJavaScript(js, lambda r, gen=generation: self._front_direct_result(r, gen))
        else:
            self._probe_standard(generation)

    def _front_direct_result(self, result, generation: int):
        if not self._active(generation):
            return
        url = str(result or "").replace("\\/", "/").replace("&amp;", "&").strip()
        low = url.lower()
        if (
            url.startswith("https://www.frontpages.com/g/")
            and f"/{self._front_slug}-" in low
            and ".webp" in low
            and not (self._front_slug == "the-washington-post" and "sports" in low)
        ):
            self._success(url, generation)
            return
        if self._probe_count < 4:
            QTimer.singleShot(900, lambda gen=generation: self._probe_front(gen))
            return
        self._probe_standard(generation)

    def _probe_standard(self, generation: int):
        if not self._active(generation) or not self.page:
            return
        expected = "WASHINGTON POST" if self._front_name == "THE WASHINGTON POST" else "VALOR ECONOMICO"
        js = STANDARD_IMAGE_JS.replace("%EXPECTED%", json.dumps(expected))
        self.page.runJavaScript(js, lambda r, gen=generation: self._standard_result(r, gen))

    def _standard_result(self, result, generation: int):
        if not self._active(generation):
            return
        raw = str(result or "").strip()
        if raw:
            try:
                data = json.loads(raw)
                url = str(data.get("url") or "").strip()
                w = int(data.get("w") or 0)
                h = int(data.get("h") or 0)
                low = url.lower()
                if (
                    url.startswith(("http://", "https://"))
                    and w >= 300
                    and h >= 450
                    and h / max(1, w) >= 1.10
                    and not (self._front_name == "THE WASHINGTON POST" and "sports" in low)
                ):
                    self._success(url, generation)
                    return
            except Exception:
                pass
        self._front_source_failed("capa principal não localizada na página", generation)

    def _front_source_failed(self, msg: str, generation: int):
        if not self._active(generation):
            return
        # Valor repete automaticamente no PressReader, como no Android.
        self._finished = True
        self._generation += 1  # invalida timers/callbacks da fonte atual
        self._start_next_front_source()

    # ---------------- helpers ----------------
    def _active(self, generation: int) -> bool:
        return not self._finished and generation == self._generation

    def _success(self, url: str, generation: int):
        if not self._active(generation):
            return
        self._finished = True
        self._generation += 1  # invalida todos os singleShot antigos
        try:
            if self.page:
                self.page.triggerAction(QWebEnginePage.Stop)
        except Exception:
            pass
        cb = self.done_cb
        self.done_cb = None
        if cb:
            cb((url or "").replace("&amp;", "&").replace("\\/", "/").strip(), None)

    def _fail(self, msg: str, generation: int):
        if not self._active(generation):
            return
        self._finished = True
        self._generation += 1
        cb = self.done_cb
        self.done_cb = None
        if cb:
            cb(None, msg)
