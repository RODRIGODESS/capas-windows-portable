# Principais Capas — Windows Portable v1.1.4 — ESTADÃO / ATÉ 10 CANDIDATAS

Base: v1.1.3. Esta versão espelha a correção Android v0.7.6.2.

## Correção principal

O clipping do Estadão pode identificar a capa com uma chamada curta como `Dark Horse __ A12`. O `A12` indica a página da matéria chamada na capa e não deve fazer o programa rejeitar a imagem.

Nesta versão:

- Apps Script envia até **10 candidatos para o Estadão** e o Windows suporta até 10; os demais jornais continuam com até 5;
- todas as posições recebidas ficam disponíveis para revisão;
- `A2`, `A3`, `A12`, `B4` etc. não derrubam automaticamente uma candidata do Estadão;
- `FUNDADO EM 1875` sozinho continua insuficiente;
- a seleção automática usa o OCR da **imagem final**;
- chamadas curtas com referência de página recebem prioridade apenas para entrar no lote;
- mantém `ABRIR PDF`, `ABRIR PASTA`, inserção manual, Valor, Washington Post e todo o motor Gmail que já funcionou.

## Apps Script

**Atualize a implantação existente** com `GmailCentralClipping-v0.7.6.2-10-CANDIDATES.gs` usando `Nova versão`. A URL `/exec` permanece a mesma e atende Android e Windows.

## GitHub Releases

O workflow continua compilando no `windows-latest` e publicando o ZIP portátil diretamente em **GitHub Releases**. A versão é lida de `version.txt` e a tag será `windows-v1.1.4`.
