# Android → Windows parity map

Base Android: `PrincipaisCapas-Android-v0.7.5.9-SAFE-BOTTOM-NAV-FIX`

| Android | Windows v1.1.0 | Regra preservada |
|---|---|---|
| `ClippingFeedClient.java` | `AppsScriptFeedResolver` + `network.py` | `/exec`, chave, `action=matters`, data `yyyy-MM-dd`, todos os links únicos consolidados por jornal |
| `CentralClippingWebResolver.java` | `CentralClippingBatchResolver` | novo Chromium por link, `Leia mais → Ver página → original_page`, máximo 5 |
| `ClippingImageScanner.java` | `ocr.py` + fluxo da UI | OCR full-page com posições, ranking 0–100, masthead no topo, publicidade, data e NYT Company |
| `FrontPageBrowserResolver.java` | `FrontPageResolver` | capa atual de Valor/Post, sem filtro de data, rejeição SPORTS, PressReader fallback do Valor |
| `PdfExporter.java` | `pdf_export.py` | JPEG 93%, largura máx. 2000, sem corte/deformação, margem individual |
| seleção manual | `models.py` + `ui.py` | inserir capa, voltar automática, navegar candidatas |
| Apps Script | `google-apps-script/GmailCentralClipping.gs` | arquivo idêntico ao APK v0.7.5.9 |

## Diferença obrigatória de plataforma

O Android usa `HttpURLConnection` e `WebView`. No Windows, a rede do Apps Script é aberta pelo Chromium do Qt para herdar proxy/certificados do Windows; o conteúdo e as regras da resposta permanecem os mesmos. Isso evita o travamento observado em `Localizando páginas no Gmail...` quando `requests` não consegue usar a mesma pilha de rede do navegador.


### v1.1.2
A fila de revisão Windows preserva os 5 slots recebidos do Apps Script. O ranking não remove candidatos da revisão.


### v1.1.3 / Android v0.7.6.1
- `ClippingImageScanner.matchesExpected` (Estadão) ↔ `app/ocr.py::matches_expected`
- `containsExactEstadaoMasthead` ↔ `contains_exact_estadao_masthead`
- `isInternalPageHeaderLine` ↔ `is_internal_page_header_line`
- Bônus de masthead + data e penalização A2/A3/A12/B4 portados com os mesmos valores.


### v1.1.4 / Android v0.7.6.2
- Limite Gmail ampliado de 5 para 10 candidatos.
- Estadão: referência A2/A3/A12/B4 em chamada de capa não é penalidade.
- Decisão final continua baseada na imagem `original_page`.
- Apps Script 0.7.6.2 é compartilhado pelas duas plataformas.


## v1.2.0 / Android v0.7.7.0
- Apps Script consolida múltiplos e-mails de Capa(s) de Jornais do mesmo dia.
- Android e Windows processam todas as candidatas consolidadas, sem corte de 5/10.


## v1.2.1 / Android v0.7.7.1
Correção sincronizada do novo padrão de assunto do Central Clipping (`CAPA DE JORNAIS N APP`) e alias `O Estado de S. Paulo - Impresso - Flip`.
