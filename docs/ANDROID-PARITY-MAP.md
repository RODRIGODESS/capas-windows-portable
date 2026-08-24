# Android → Windows parity map

Base Android: `PrincipaisCapas-Android-v0.7.5.9-SAFE-BOTTOM-NAV-FIX`

| Android | Windows v1.1.0 | Regra preservada |
|---|---|---|
| `ClippingFeedClient.java` | `AppsScriptFeedResolver` + `network.py` | `/exec`, chave, `action=matters`, data `yyyy-MM-dd`, até 5 links por jornal |
| `CentralClippingWebResolver.java` | `CentralClippingBatchResolver` | novo Chromium por link, `Leia mais → Ver página → original_page`, máximo 5 |
| `ClippingImageScanner.java` | `ocr.py` + fluxo da UI | OCR full-page com posições, ranking 0–100, masthead no topo, publicidade, data e NYT Company |
| `FrontPageBrowserResolver.java` | `FrontPageResolver` | capa atual de Valor/Post, sem filtro de data, rejeição SPORTS, PressReader fallback do Valor |
| `PdfExporter.java` | `pdf_export.py` | JPEG 93%, largura máx. 2000, sem corte/deformação, margem individual |
| seleção manual | `models.py` + `ui.py` | inserir capa, voltar automática, navegar candidatas |
| Apps Script | `google-apps-script/GmailCentralClipping.gs` | arquivo idêntico ao APK v0.7.5.9 |

## Diferença obrigatória de plataforma

O Android usa `HttpURLConnection` e `WebView`. No Windows, a rede do Apps Script é aberta pelo Chromium do Qt para herdar proxy/certificados do Windows; o conteúdo e as regras da resposta permanecem os mesmos. Isso evita o travamento observado em `Localizando páginas no Gmail...` quando `requests` não consegue usar a mesma pilha de rede do navegador.
