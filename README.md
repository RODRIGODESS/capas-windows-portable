# Principais Capas Windows Portable v1.2.0 — MULTI EMAIL CONSOLIDATION

Base: v1.1.4.

## Alteração desta versão

A ponte Gmail agora consolida todos os e-mails da data cujo assunto seja `Monitoramento: Capa(s) de Jornais`, aceitando também sufixos numéricos como `1`, `2`, `3` e espaços diferentes ao redor de `:`.

Todos os links `Leia mais` encontrados nos vários e-mails são reunidos por jornal. Só URLs realmente idênticas são deduplicadas. O Windows não corta mais a lista em 10 candidatas: todas as candidatas entregues pelo Apps Script são resolvidas, ranqueadas pela imagem final e ficam disponíveis em revisão.

O timeout do Apps Script pelo Chromium foi ampliado para 45 s para acomodar a consolidação de vários boletins.

## Apps Script

Atualize a implantação existente com `GmailCentralClipping-v0.7.7.0-MULTI-EMAIL.gs`. A URL `/exec` não muda.

## Preservado

Motor equivalente ao Android, Central Clipping, Valor Econômico, Washington Post, OCR, seleção automática, revisão manual, inserção manual, PDF otimizado, Abrir PDF/Abrir Pasta e publicação direta em GitHub Releases.
