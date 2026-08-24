from __future__ import annotations
import json, re, time
from dataclasses import dataclass
from typing import Callable
from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile

ORIG_JS = r"""
(function(){
 function clean(u){if(!u)return '';try{return new URL(String(u).replace(/\\\//g,'/').replace(/&amp;/g,'&'),document.baseURI).href}catch(e){return String(u||'')}}
 function ok(u){u=String(u||'').toLowerCase();return u.indexOf('/original_page/')>=0||u.indexOf('static.resources/original_page/')>=0}
 try{var pe=performance.getEntriesByType('resource')||[];for(var i=0;i<pe.length;i++){var u=clean(pe[i].name);if(ok(u))return u}}catch(e){}
 try{var els=document.querySelectorAll('*');var aa=['href','src','data-src','data-url','data-image','data-original','data-page','onclick'];for(var j=0;j<els.length;j++){for(var k=0;k<aa.length;k++){var v=clean(els[j].getAttribute(aa[k]));if(ok(v))return v}}}catch(e){}
 try{var html=document.documentElement.innerHTML.replace(/&amp;/g,'&').replace(/\\\//g,'/');var m=html.match(/https?:[^\"'<>\\s]+\/original_page\/[^\"'<>\\s]+/i);if(m)return m[0]}catch(e){}
 return '';
})()
"""

CLICK_VER_PAGINA_JS = r"""
(function(){
 function n(s){return (s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase()}
 var all=document.querySelectorAll('a,button,[role=button]');
 for(var i=0;i<all.length;i++){var t=n(all[i].innerText||all[i].textContent||all[i].getAttribute('aria-label')||'');if(t.indexOf('VER PAGINA')>=0){all[i].click();return true}}
 return false;
})()
"""

CURRENT_WEBP_JS = r"""
(function(slug){
 function pick(u){try{u=String(u||'');var l=u.toLowerCase();if(l.indexOf('/g/')<0||l.indexOf('/'+slug+'-')<0||l.indexOf('.webp')<0)return '';if(slug==='the-washington-post'&&l.indexOf('sports')>=0)return '';var p=l.indexOf('/g/'),e=l.indexOf('.webp',p);if(p<0||e<0)return '';var x=u.substring(p,e+5);if(x.indexOf('/g/')===0)x='https://www.frontpages.com'+x;return x}catch(e){return ''}}
 try{var rr=performance.getEntriesByType('resource')||[];for(var i=0;i<rr.length;i++){var v=pick(rr[i].name);if(v)return v}}catch(e){}
 try{var imgs=document.images||[];for(var j=0;j<imgs.length;j++){var im=imgs[j],v=pick(im.currentSrc||im.src);if(v)return v;var aa=['src','data-src','data-lazy-src','data-original','data-image','data-url','data-full'];for(var a=0;a<aa.length;a++){v=pick(im.getAttribute(aa[a]));if(v)return v}var ss=(im.getAttribute('srcset')||im.getAttribute('data-srcset')||'').split(',');for(var k=0;k<ss.length;k++){v=pick(ss[k].trim().split(/\s+/)[0]);if(v)return v}}}catch(e){}
 try{var html=document.documentElement.innerHTML;var low=html.toLowerCase(),key='/'+slug+'-',pos=low.indexOf(key);while(pos>=0){var gp=low.lastIndexOf('/g/',pos),we=low.indexOf('.webp',pos);if(gp>=0&&we>pos){var x=html.substring(gp,we+5).replace(/&amp;/g,'&').replace(/\\\//g,'/');if(x.indexOf('/g/')===0)x='https://www.frontpages.com'+x;if(!(slug==='the-washington-post'&&x.toLowerCase().indexOf('sports')>=0))return x}pos=low.indexOf(key,pos+key.length)}}catch(e){}
 return '';
})(%SLUG%)
"""

class CapturePage(QWebEnginePage):
    captured = Signal(str)
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        s=url.toString()
        if "/original_page/" in s:
            self.captured.emit(s)
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)
    def createWindow(self, _type):
        return self

class Resolver(QObject):
    progress = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile = QWebEngineProfile(self)
        self.profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36")
        self.page = None
        self.done_cb = None
        self.timeout = None
        self._finished = False

    def _new_page(self):
        if self.page:
            self.page.deleteLater()
        self.page = CapturePage(self.profile, self)
        self.page.captured.connect(self._success)
        return self.page

    def resolve_original(self, matter_url: str, callback: Callable[[str|None, str|None], None]):
        self.done_cb=callback; self._finished=False
        page=self._new_page()
        self.progress.emit("Abrindo página do Central Clipping…")
        page.loadFinished.connect(lambda ok:self._after_load_original(ok))
        page.load(QUrl(matter_url))
        self.timeout=QTimer.singleShot(13000, lambda:self._fail("timeout ao localizar Ver página"))

    def _after_load_original(self, ok):
        if self._finished: return
        if not ok:
            self._fail("falha ao abrir o link do clipping"); return
        QTimer.singleShot(350, self._probe_original)

    def _probe_original(self):
        if self._finished or not self.page: return
        self.page.runJavaScript(ORIG_JS, self._original_probe_result)

    def _original_probe_result(self, result):
        if self._finished: return
        if result and isinstance(result,str) and "/original_page/" in result:
            self._success(result); return
        self.page.runJavaScript(CLICK_VER_PAGINA_JS, lambda clicked: QTimer.singleShot(900, self._probe_original))

    def resolve_frontpages(self, slug: str, callback: Callable[[str|None,str|None],None]):
        self.done_cb=callback; self._finished=False
        page=self._new_page()
        page_url=f"https://www.frontpages.com/{slug}/"
        self.progress.emit("Abrindo FrontPages…")
        page.loadFinished.connect(lambda ok:self._after_load_front(ok,slug))
        page.load(QUrl(page_url))
        QTimer.singleShot(15000, lambda:self._fail("timeout do navegador interno"))

    def _after_load_front(self, ok, slug):
        if self._finished:return
        if not ok:
            self._fail("falha ao abrir FrontPages");return
        js=CURRENT_WEBP_JS.replace("%SLUG%", json.dumps(slug))
        QTimer.singleShot(500, lambda:self.page.runJavaScript(js, lambda r:self._front_result(r,js)))

    def _front_result(self, result, js):
        if self._finished:return
        if result and isinstance(result,str) and ".webp" in result.lower():
            self._success(result);return
        QTimer.singleShot(1200, lambda:self.page.runJavaScript(js, lambda r:self._front_second(r)))

    def _front_second(self,result):
        if result and isinstance(result,str) and ".webp" in result.lower(): self._success(result)
        else:self._fail("capa atual não localizada no link")

    def _success(self,url):
        if self._finished:return
        self._finished=True
        cb=self.done_cb; self.done_cb=None
        if cb: cb(url,None)

    def _fail(self,msg):
        if self._finished:return
        self._finished=True
        cb=self.done_cb; self.done_cb=None
        if cb: cb(None,msg)
