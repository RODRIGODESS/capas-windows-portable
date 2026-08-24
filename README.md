# Principais Capas — Windows Portable v1.1.0 FULL ANDROID PORT

Esta versão foi reconstruída a partir da base Android **v0.7.5.9** com portabilidade módulo a módulo, em vez de apenas reproduzir visualmente o fluxo.

## Correção principal

A v1.0.x ficava presa em `Localizando páginas no Gmail...` porque a ponte Apps Script era consultada por `requests`, enquanto a navegação de Valor/Post usava Chromium. Em alguns Windows/proxies corporativos essas duas pilhas de rede não se comportam igual.

Na v1.1.0 o Apps Script também é consultado pelo Chromium interno do aplicativo, com User-Agent e fluxo equivalentes ao Android. Há timeout explícito de 32 s; o estado não pode ficar indefinidamente em “Localizando”.

## Paridade com Android

- Gmail/Apps Script oficial embutido.
- Até 5 páginas por jornal.
- `Leia mais → Ver página → original_page` em navegador novo para cada candidata.
- Ranking de capa portado do `ClippingImageScanner`: OCR de página completa com posição das linhas, masthead no topo, data, sinais de publicidade e proteção especial do NYT.
- Valor Econômico: capa exibida atualmente no FrontPages, PressReader como fallback, sem busca em fins de semana.
- Washington Post: capa exibida atualmente no FrontPages e rejeição de `SPORTS`.
- Cookies da sessão Chromium são repassados ao download direto de FrontPages, como o `CookieManager` faz no Android.
- Revisão manual das candidatas, inserção manual e retorno à automática.
- PDF otimizado igual ao Android: JPEG 93%, largura máx. 2000 px, sem crop ou deformação.
- Apps Script dentro do projeto é byte-a-byte igual ao usado no APK base.

Veja `docs/ANDROID-PARITY-MAP.md`.

## Build / Release

O GitHub Actions gera o portable em `windows-latest` e publica diretamente em **GitHub Releases** com a tag `windows-v1.1.0`.
