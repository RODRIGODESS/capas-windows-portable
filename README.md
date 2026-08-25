# Principais Capas — Windows Portable v1.1.3 ESTADÃO COVER RANKING FIX

Esta versão foi reconstruída a partir da base Android **v0.7.5.9** com portabilidade módulo a módulo, em vez de apenas reproduzir visualmente o fluxo.

## Correção principal

A v1.0.x ficava presa em `Localizando páginas no Gmail...` porque a ponte Apps Script era consultada por `requests`, enquanto a navegação de Valor/Post usava Chromium. Em alguns Windows/proxies corporativos essas duas pilhas de rede não se comportam igual.

Na base v1.1.2 o Apps Script também é consultado pelo Chromium interno do aplicativo, com User-Agent e fluxo equivalentes ao Android. Há timeout explícito de 32 s; o estado não pode ficar indefinidamente em “Localizando”.

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

O GitHub Actions gera o portable em `windows-latest` e publica diretamente em **GitHub Releases** com a tag `windows-v1.1.3`.


## v1.1.1 - Pós-geração do PDF

Ao concluir a geração do PDF, o aplicativo agora oferece três opções:

- **ABRIR PDF** — abre o PDF gerado.
- **ABRIR PASTA** — abre diretamente a pasta onde o PDF foi salvo.
- **FECHAR** — fecha a confirmação e mantém o aplicativo aberto.

Esta versão foi criada diretamente sobre a v1.1.0 funcional e não altera os motores de Gmail/Apps Script, Central Clipping, Valor Econômico, Washington Post, OCR, ranking das candidatas ou geração do conteúdo do PDF.


## v1.1.2 - Mostrar todas as páginas recebidas do Gmail

- Se o Apps Script enviar 5 páginas, a revisão mostra **5 de 5**, sem esconder candidatas por pontuação.
- Removida a deduplicação de `original_page`: cada item recebido mantém sua própria posição.
- A ordem original 1..5 do Gmail é preservada.
- Se uma imagem não conseguir abrir, o slot continua visível com diagnóstico em vez de desaparecer.
- O ranking automático escolhe somente entre imagens realmente abertas.
- Anterior/Próxima navegam sem alterar a capa escolhida até clicar em **USAR ESTA PÁGINA**.
- Motor Gmail, Valor, Washington Post e PDF da v1.1.1 foram preservados.


## v1.1.3 - Correção de seleção automática do Estadão

Esta versão espelha no Windows a correção aplicada ao Android v0.7.6.1:

- `FUNDADO EM 1875` sozinho não é mais tratado como masthead do Estadão.
- `O ESTADO DE S. PAULO` no topo + a data selecionada recebe prioridade forte.
- Marcadores de página interna como `A2`, `A3`, `A12`, `B4` no cabeçalho reduzem a confiança.
- As 5 candidatas recebidas do Gmail continuam disponíveis em revisão.
- Nenhuma alteração foi feita no Apps Script, Valor, Washington Post, PDF ou inserção manual.

A partir desta versão, correções funcionais do projeto devem ser aplicadas em paralelo às versões Android e Windows, preservando as particularidades de cada plataforma.
