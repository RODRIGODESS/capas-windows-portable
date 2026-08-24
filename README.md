# Principais Capas — Windows Portable v1.0.2

Base funcional: Android **v0.7.5.9 SAFE BOTTOM NAV FIX**.

## Correção principal desta versão

A v1.0.1 reproduzia a lógica do Android, mas o navegador interno do Windows criava apenas um `QWebEnginePage` sem uma `QWebEngineView` realmente anexada. Isso pode impedir ou atrasar `lazy-load`, `window.open` e recursos da página — justamente o que o Central Clipping usa no fluxo **Leia mais → Ver página → original_page**, e o que o FrontPages usa para revelar o WEBP da capa.

Na v1.0.2 o motor foi refeito para seguir o processo real do Android:

1. o Apps Script recebe `action=matters&date=AAAA-MM-DD` com a mesma chave e o mesmo `/exec` do APK;
2. recebe até 5 links `Leia mais` por jornal;
3. um resolver em lote equivalente ao `CentralClippingWebResolver.java` abre cada link;
4. **cada candidata ganha uma nova view Chromium realmente anexada à janela, fora da tela**, como a WebView 2×2 adicionada à Activity no Android;
5. procura `original_page` nos recursos, atributos, HTML e botão **Ver página**;
6. navega/clica e intercepta o URL original;
7. baixa e analisa até 5 páginas, mantendo todas para revisão e escolhendo a maior pontuação;
8. jornais do Gmail não usam fallback da internet.

Valor Econômico e Washington Post também usam uma view Chromium anexada e o **mesmo User-Agent móvel** do Android. A lógica continua sendo:

- Washington Post: capa exibida atualmente no FrontPages; rejeita SPORTS;
- Valor: capa exibida atualmente no FrontPages; PressReader como fallback;
- Valor não é buscado em fim de semana.

## Apps Script embutido

O endereço oficial já vem configurado:

`https://script.google.com/macros/s/AKfycbwO46cUIb0O--6_LUrysIjhCAlJJqjw0PRCuRLOTndiy4BkFZhNbXPQgA3rc9H8YC5l/exec`

A v1.0.2 aplica esse endereço uma vez ao migrar de versões anteriores, igual ao mecanismo de migração do Android. Depois disso ele continua editável no aplicativo.

O arquivo `google-apps-script/GmailCentralClipping.gs` é o mesmo usado pelo Android v0.7.5.9.

## GitHub Releases

O workflow `.github/workflows/build-windows-portable.yml` compila no `windows-latest`, cria o ZIP portátil e publica **diretamente em GitHub Releases**.

Release esperada: `windows-v1.0.2`.

Arquivo esperado: `PrincipaisCapas-Windows-Portable-v1.0.2.zip`.

## Teste recomendado

Use 24/08/2026 para comparar com o APK Android. O fluxo esperado é:

- `Localizando páginas no Gmail…`
- `Gmail enviou X página(s) • abrindo Ver página…`
- `Gmail X recebida(s) • Y aberta(s)`
- `candidata N/X escolhida • confiança ...`

Valor e Washington Post rodam em paralelo, sem bloquear o Gmail.
