# Principais Capas Windows Portable v1.2.3 — VALOR PRESSREADER FULL COVER

Base: v1.2.2.

## Correção definitiva do Valor Econômico
- Remove o FrontPages da busca automática do **Valor Econômico**.
- O Valor passa a usar **PressReader como fonte automática exclusiva**, evitando aceitar arquivos que já chegam recortados na origem.
- Se o PressReader não entregar a página inteira, o programa **não aceita uma capa duvidosa** e mantém o Valor pendente para inserção manual.
- Prévia e PDF continuam preservando a imagem inteira, sem crop e sem deformação.
- Gmail/Central Clipping, múltiplos e-mails, Washington Post, revisão de candidatas, inserção manual e exportação do PDF foram preservados.
- Não exige alteração no Apps Script; a implantação v0.7.7.1 continua válida.
- GitHub Actions continua publicando o ZIP diretamente em Releases.

---

# Principais Capas Windows Portable v1.2.2 — VALOR FULL COVER RESTORE

Base: v1.2.1.

## Correção
- Corrige regressão em que o Valor Econômico podia ser aceito a partir de uma imagem recortada do FrontPages.
- O FrontPages continua sendo a primeira tentativa.
- Se a imagem baixada tiver proporção típica de crop/miniatura, ela é descartada e o app tenta automaticamente o PressReader.
- A prévia usa KeepAspectRatio e o PDF mantém a imagem inteira, sem crop nem deformação.
- Gmail/Central Clipping, múltiplos e-mails, Washington Post, revisão de candidatas, inserção manual e PDF não foram alterados.
- Não exige alteração no Apps Script; a implantação v0.7.7.1 continua válida.
- GitHub Actions continua publicando o ZIP diretamente em Releases.

# Principais Capas Windows Portable v1.2.1 — NEW CENTRAL CLIPPING SUBJECT FIX

Base: v1.1.4.

## Alteração desta versão

A ponte Gmail agora consolida todos os e-mails da data cujo assunto seja `Monitoramento: Capa(s) de Jornais`, aceitando também sufixos numéricos como `1`, `2`, `3` e espaços diferentes ao redor de `:`.

Todos os links `Leia mais` encontrados nos vários e-mails são reunidos por jornal. Só URLs realmente idênticas são deduplicadas. O Windows não corta mais a lista em 10 candidatas: todas as candidatas entregues pelo Apps Script são resolvidas, ranqueadas pela imagem final e ficam disponíveis em revisão.

O timeout do Apps Script pelo Chromium foi ampliado para 45 s para acomodar a consolidação de vários boletins.

## Apps Script

Atualize a implantação existente com `GmailCentralClipping-v0.7.7.1-NEW-SUBJECT-FIX.gs`. A URL `/exec` não muda.

## Preservado

Motor equivalente ao Android, Central Clipping, Valor Econômico, Washington Post, OCR, seleção automática, revisão manual, inserção manual, PDF otimizado, Abrir PDF/Abrir Pasta e publicação direta em GitHub Releases.


## v1.2.1
- Espelha o Android v0.7.7.1.
- Aceita o novo assunto `CAPA DE JORNAIS 1 APP` e mantém suporte aos assuntos antigos/numerados.
- Adiciona o alias `O Estado de S. Paulo - Impresso - Flip` ao Estadão no Apps Script.
- Mantém o mesmo `/exec` oficial e publicação direta em GitHub Releases.
