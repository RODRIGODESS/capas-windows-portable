from __future__ import annotations
import os, shutil
from datetime import date, datetime
from pathlib import Path
from PIL import Image
from PySide6.QtCore import Qt, QSize, QThreadPool, Signal, QObject, QUrl
from PySide6.QtGui import QIcon, QPixmap, QColor, QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QCheckBox,
    QListWidget,QListWidgetItem,QStackedWidget,QDateEdit,QFrame,QScrollArea,QFileDialog,
    QMessageBox,QProgressBar,QDialog,QDialogButtonBox,QLineEdit,QGroupBox,QSizePolicy
)
from .config import bundle_dir, cache_dir, downloads_dir, GMAIL_PAPERS, WEB_PAPERS, load_settings, save_settings
from .models import CandidatePage
from .network import fetch_matters, download_image, safe_slug
from .newspapers import load_entries
from .ocr import score_candidate
from .pdf_export import export_pdf, build_filename
from .workers import Worker
from .web_resolver import Resolver

STYLE = """
QMainWindow,QWidget{background:#071625;color:#eaf3ff;font-family:'Segoe UI';font-size:13px}
QFrame#header{background:#0b2948;border:1px solid #284867;border-radius:14px}
QFrame#card{background:#0b1f33;border:1px solid #29445f;border-radius:12px}
QLabel#title{font-size:24px;font-weight:700;color:white}
QLabel#sub{color:#8fa9c3}
QLabel#green{color:#53e879}
QPushButton{background:#0d2943;border:1px solid #315675;border-radius:9px;padding:9px 14px;color:#eaf3ff;font-weight:600}
QPushButton:hover{background:#123858}
QPushButton#primary{background:#176fc1;border-color:#2d8cff}
QPushButton#greenBtn{background:#1d8f50;border-color:#39b76d}
QPushButton#danger{background:#48202a;border-color:#733443}
QCheckBox{spacing:8px}
QListWidget{background:#081827;border:1px solid #203b56;border-radius:11px;padding:4px;outline:none}
QListWidget::item{padding:9px;border-radius:8px;margin:2px}
QListWidget::item:selected{background:#0d3152;border:1px solid #2d8cff}
QDateEdit,QLineEdit{background:#0c2034;border:1px solid #315675;border-radius:8px;padding:8px;color:white}
QProgressBar{border:0;background:#0c2034;border-radius:3px;height:6px} QProgressBar::chunk{background:#2d8cff;border-radius:3px}
QGroupBox{border:1px solid #29445f;border-radius:10px;margin-top:12px;padding-top:12px;font-weight:600}
QGroupBox::title{subcontrol-origin:margin;left:10px;padding:0 6px;color:#b9cbe0}
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Principais Capas — Windows Portable")
        self.setWindowIcon(QIcon(str(bundle_dir()/"assets"/"app_icon.ico")))
        self.resize(1320,820); self.setMinimumSize(1050,680)
        self.setStyleSheet(STYLE)
        self.entries=load_entries(); self.settings=load_settings(); self.threadpool=QThreadPool.globalInstance()
        self.resolver=Resolver(self); self.resolver.progress.connect(self.set_status)
        self.queue=[]; self.last_pdf=None; self.current_entry=None
        self._build(); self._refresh_list(); self._select_row(0)

    def _build(self):
        central=QWidget(); self.setCentralWidget(central); root=QVBoxLayout(central); root.setContentsMargins(12,12,12,12); root.setSpacing(8)
        header=QFrame(); header.setObjectName("header"); hl=QHBoxLayout(header); hl.setContentsMargins(14,10,14,10)
        icon=QLabel(); icon.setPixmap(QPixmap(str(bundle_dir()/"assets"/"app_icon.png")).scaled(54,54,Qt.KeepAspectRatio,Qt.SmoothTransformation)); hl.addWidget(icon)
        tt=QVBoxLayout(); title=QLabel("PRINCIPAIS CAPAS"); title.setObjectName("title"); tt.addWidget(title); sub=QLabel("Windows Portable • busca automática • revisão manual • PDF otimizado"); sub.setObjectName("sub"); tt.addWidget(sub); hl.addLayout(tt,1)
        self.date_edit=QDateEdit(); self.date_edit.setCalendarPopup(True); self.date_edit.setDate(datetime.now().date()); self.date_edit.setDisplayFormat("dd/MM/yyyy"); hl.addWidget(QLabel("Data:")); hl.addWidget(self.date_edit)
        cfg=QPushButton("⚙ Apps Script"); cfg.clicked.connect(self.configure_script); hl.addWidget(cfg)
        root.addWidget(header)

        actions=QHBoxLayout();
        self.refresh_btn=QPushButton("↻  ATUALIZAR CAPAS"); self.refresh_btn.setObjectName("primary"); self.refresh_btn.clicked.connect(self.refresh_all); actions.addWidget(self.refresh_btn)
        self.pdf_btn=QPushButton("▣  GERAR PDF"); self.pdf_btn.setObjectName("greenBtn"); self.pdf_btn.clicked.connect(self.generate_pdf); actions.addWidget(self.pdf_btn)
        self.open_btn=QPushButton("▤  ABRIR PDF GERADO"); self.open_btn.clicked.connect(self.open_pdf); actions.addWidget(self.open_btn)
        allb=QPushButton("✓ Marcar todas"); allb.clicked.connect(lambda:self.set_all(True)); actions.addWidget(allb)
        noneb=QPushButton("× Desmarcar"); noneb.clicked.connect(lambda:self.set_all(False)); actions.addWidget(noneb)
        root.addLayout(actions)
        self.progress=QProgressBar(); self.progress.setRange(0,0); self.progress.hide(); root.addWidget(self.progress)

        content=QHBoxLayout(); content.setSpacing(10); root.addLayout(content,1)
        left=QFrame(); left.setObjectName("card"); ll=QVBoxLayout(left); ll.addWidget(QLabel("JORNAIS (8)"))
        self.list=QListWidget(); self.list.currentRowChanged.connect(self._select_row); ll.addWidget(self.list,1); content.addWidget(left,38)
        right=QFrame(); right.setObjectName("card"); rl=QVBoxLayout(right); self.paper_title=QLabel("Selecione um jornal"); self.paper_title.setObjectName("title"); rl.addWidget(self.paper_title)
        self.paper_status=QLabel(""); self.paper_status.setObjectName("green"); self.paper_status.setWordWrap(True); rl.addWidget(self.paper_status)
        self.preview=QLabel("Aguardando capa"); self.preview.setAlignment(Qt.AlignCenter); self.preview.setMinimumHeight(360); self.preview.setStyleSheet("background:#061321;border:1px solid #29445f;border-radius:10px;color:#8fa9c3"); rl.addWidget(self.preview,1)
        candbox=QGroupBox("Páginas recebidas / candidatas"); cl=QHBoxLayout(candbox); self.prev_btn=QPushButton("◀ Anterior"); self.prev_btn.clicked.connect(lambda:self.move_candidate(-1)); cl.addWidget(self.prev_btn); self.cand_label=QLabel("0 de 0"); self.cand_label.setAlignment(Qt.AlignCenter); cl.addWidget(self.cand_label,1); self.next_btn=QPushButton("Próxima ▶"); self.next_btn.clicked.connect(lambda:self.move_candidate(1)); cl.addWidget(self.next_btn); rl.addWidget(candbox)
        ba=QHBoxLayout(); review=QPushButton("USAR ESTA PÁGINA"); review.setObjectName("primary"); review.clicked.connect(self.use_current_candidate); ba.addWidget(review); manual=QPushButton("INSERIR CAPA MANUALMENTE"); manual.clicked.connect(self.manual_cover); ba.addWidget(manual); restore=QPushButton("VOLTAR PARA AUTOMÁTICA"); restore.clicked.connect(self.restore_auto); ba.addWidget(restore); rl.addLayout(ba)
        content.addWidget(right,62)
        self.statusBar().showMessage("Pronto")

    def target_date(self):
        q=self.date_edit.date(); return date(q.year(),q.month(),q.day())

    def set_status(self,msg): self.statusBar().showMessage(msg)
    def set_busy(self,b):
        self.progress.setVisible(b); self.refresh_btn.setEnabled(not b); self.pdf_btn.setEnabled(not b)

    def _refresh_list(self):
        row=self.list.currentRow(); self.list.clear()
        for e in self.entries:
            item=QListWidgetItem(); item.setData(Qt.UserRole,e.name); self.list.addItem(item)
            w=QWidget(); l=QHBoxLayout(w); l.setContentsMargins(6,4,6,4)
            cb=QCheckBox(); cb.setChecked(e.selected); cb.toggled.connect(lambda v,en=e:self._toggle(en,v)); l.addWidget(cb)
            num=QLabel(str(self.entries.index(e)+1)); num.setFixedWidth(28); num.setStyleSheet("font-size:16px;font-weight:700;color:#8fb9e6"); l.addWidget(num)
            tx=QVBoxLayout(); nm=QLabel(e.name); nm.setStyleSheet("font-size:15px;font-weight:700;color:white"); tx.addWidget(nm); st=QLabel(e.status); st.setObjectName("sub"); st.setWordWrap(True); tx.addWidget(st); l.addLayout(tx,1)
            if e.current_path:
                pm=QPixmap(str(e.current_path)).scaled(48,68,Qt.KeepAspectRatio,Qt.SmoothTransformation); thumb=QLabel(); thumb.setPixmap(pm); l.addWidget(thumb)
            item.setSizeHint(QSize(300,78)); self.list.setItemWidget(item,w)
        if self.entries:
            self.list.setCurrentRow(max(0,min(row if row>=0 else 0,len(self.entries)-1)))

    def _toggle(self,e,v): e.selected=v
    def set_all(self,v):
        for e in self.entries:e.selected=v
        self._refresh_list()

    def _select_row(self,row):
        if not (0<=row<len(self.entries)):return
        self.current_entry=self.entries[row]; self._show_entry()

    def _show_entry(self):
        e=self.current_entry
        if not e:return
        self.paper_title.setText(e.name); self.paper_status.setText(e.status)
        p=e.current_path
        if p and p.exists(): self.preview.setPixmap(QPixmap(str(p)).scaled(self.preview.size()-QSize(18,18),Qt.KeepAspectRatio,Qt.SmoothTransformation)); self.preview.setText("")
        else: self.preview.setPixmap(QPixmap()); self.preview.setText("Aguardando capa")
        n=len(e.candidates); idx=e.chosen_index if e.chosen_index>=0 else 0; self.cand_label.setText(f"{idx+1 if n else 0} de {n}" + (" • MANUAL" if e.is_manual else "")); self.prev_btn.setEnabled(n>1); self.next_btn.setEnabled(n>1)

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self.current_entry:self._show_entry()

    def move_candidate(self,step):
        e=self.current_entry; n=len(e.candidates) if e else 0
        if n<1:return
        idx=e.chosen_index if e.chosen_index>=0 else 0; idx=(idx+step)%n; e.choose(idx); e.status=f"Candidata {idx+1}/{n} selecionada • confiança {e.candidates[idx].confidence}%"; self._show_entry(); self._refresh_list()

    def use_current_candidate(self):
        e=self.current_entry
        if not e or not e.candidates:return
        idx=max(0,e.chosen_index); e.choose(idx); e.status=f"Candidata {idx+1}/{len(e.candidates)} escolhida • confiança {e.candidates[idx].confidence}%"; self._show_entry(); self._refresh_list()

    def manual_cover(self):
        e=self.current_entry
        if not e:return
        fn,_=QFileDialog.getOpenFileName(self,"Inserir capa manualmente","","Imagens (*.jpg *.jpeg *.png *.webp *.bmp)")
        if not fn:return
        e.set_manual(Path(fn)); self._show_entry(); self._refresh_list()

    def restore_auto(self):
        e=self.current_entry
        if not e:return
        e.restore_automatic(); self._show_entry(); self._refresh_list()

    def configure_script(self):
        dlg=QDialog(self); dlg.setWindowTitle("Apps Script"); lay=QVBoxLayout(dlg); lay.addWidget(QLabel("URL /exec do Apps Script:")); edit=QLineEdit(self.settings.get("apps_script_url","")); lay.addWidget(edit); bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); lay.addWidget(bb); bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject)
        if dlg.exec(): self.settings["apps_script_url"]=edit.text().strip(); save_settings(self.settings); QMessageBox.information(self,"Apps Script","URL salva.")

    def refresh_all(self):
        self.set_busy(True); self.set_status("Consultando Gmail / Apps Script…")
        for e in self.entries:
            e.status="Aguardando"; e.candidates=[]; e.chosen_index=-1; e.manual_path=None
        self._refresh_list()
        w=Worker(fetch_matters,self.settings.get("apps_script_url",""),self.target_date()); w.signals.finished.connect(self._feed_ready); w.signals.error.connect(self._feed_error); self.threadpool.start(w)

    def _feed_error(self,msg):
        # Ainda tenta Valor/Post, porque são fontes independentes do Gmail.
        self.set_status("Gmail: "+msg); self.queue=[]; self._enqueue_web_papers(); self._process_queue()

    def _feed_ready(self,result):
        matters,meta=result; self.queue=[]
        for e in self.entries:
            if e.name in GMAIL_PAPERS:
                urls=matters.get(e.name,[])[:5]
                if not urls:e.status="Gmail: nenhuma página recebida"
                for i,u in enumerate(urls): self.queue.append(("gmail",e,u,i+1))
        self._enqueue_web_papers(); self._process_queue()

    def _enqueue_web_papers(self):
        for e in self.entries:
            if e.name=="VALOR ECONÔMICO" and self.target_date().weekday()>=5:
                e.status="Sem edição regular no fim de semana"; continue
            if e.name=="VALOR ECONÔMICO": self.queue.insert(0,("front",e,"valor-economico",1))
            elif e.name=="THE WASHINGTON POST": self.queue.insert(0,("front",e,"the-washington-post",1))

    def _process_queue(self):
        if not self.queue:
            self._finalize_refresh(); return
        kind,e,value,idx=self.queue.pop(0)
        if kind=="gmail":
            self.set_status(f"{e.name}: abrindo candidata {idx}…")
            self.resolver.resolve_original(value, lambda url,err:self._resolved_url(e,url,err,value,idx))
        else:
            self.set_status(f"{e.name}: buscando capa atual…")
            self.resolver.resolve_frontpages(value, lambda url,err:self._resolved_url(e,url,err,f"https://www.frontpages.com/{value}/",idx))

    def _resolved_url(self,e,url,err,referer,idx):
        if not url:
            if not e.candidates:e.status=f"Falha: {err}"; self._refresh_list(); self._process_queue(); return
        ext=".webp" if ".webp" in url.lower() else ".jpg"; dest=cache_dir()/self.target_date().isoformat()/f"{safe_slug(e.name)}-{idx}{ext}"
        w=Worker(self._download_and_score,url,dest,referer,e.name,e.mastheads)
        w.signals.finished.connect(lambda c,en=e:self._candidate_ready(en,c)); w.signals.error.connect(lambda m,en=e:self._candidate_error(en,m)); self.threadpool.start(w)

    def _download_and_score(self,url,dest,referer,name,mastheads):
        download_image(url,dest,referer); score,conf,text=score_candidate(dest,name,mastheads); return CandidatePage(dest,score,conf,text,url)

    def _candidate_ready(self,e,c):
        e.candidates.append(c); e.candidates.sort(key=lambda x:x.score,reverse=True); e.chosen_index=0; e.automatic_index=0; best=e.candidates[0]; e.status=f"{len(e.candidates)} candidata(s) aberta(s) • confiança {best.confidence}%"; self._refresh_list(); self._show_entry(); self._process_queue()

    def _candidate_error(self,e,msg):
        if not e.candidates:e.status="Falha ao baixar capa: "+msg
        self._refresh_list(); self._process_queue()

    def _finalize_refresh(self):
        self.set_busy(False); self.set_status("Atualização concluída")
        for e in self.entries:
            if e.candidates:
                e.candidates.sort(key=lambda x:x.score,reverse=True); e.chosen_index=0; e.automatic_index=0; e.status=f"Candidata 1/{len(e.candidates)} escolhida • confiança {e.candidates[0].confidence}%"
        self._refresh_list(); self._show_entry()

    def generate_pdf(self):
        try:
            p=export_pdf(self.entries,self.target_date()); self.last_pdf=p; QMessageBox.information(self,"PDF gerado",f"PDF salvo em:\n{p}")
        except Exception as e: QMessageBox.critical(self,"Erro ao gerar PDF",str(e))

    def open_pdf(self):
        p=self.last_pdf or (downloads_dir()/build_filename(self.target_date()))
        if not Path(p).exists(): QMessageBox.warning(self,"PDF","Nenhum PDF encontrado para a data selecionada."); return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))
