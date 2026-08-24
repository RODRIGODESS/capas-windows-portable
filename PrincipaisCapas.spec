# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from pathlib import Path

root=Path(SPECPATH)
hidden=collect_submodules('PySide6.QtWebEngineCore')+collect_submodules('PySide6.QtWebEngineWidgets')
datas=[
    (str(root/'assets'),'assets'),
    (str(root/'version.txt'),'.'),
]
if (root/'vendor'/'tesseract').exists():
    datas.append((str(root/'vendor'/'tesseract'),'tesseract'))

a=Analysis(['main.py'], pathex=[str(root)], binaries=[], datas=datas, hiddenimports=hidden,
           hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='PrincipaisCapas',debug=False,bootloader_ignore_signals=False,
        strip=False,upx=True,console=False,icon=str(root/'assets'/'app_icon.ico'))
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=True,upx_exclude=[],name='PrincipaisCapas-Portable')
