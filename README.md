# Principais Capas — Windows Portable v1.0.1

Versão de correção do motor de busca para trabalhar no Windows com o mesmo fluxo funcional da base Android v0.7.5.9.

## O que mudou na v1.0.1

- Gmail/Apps Script e Valor/Washington Post agora iniciam **em paralelo**.
- O timeout de Washington Post/Valor não bloqueia mais O Globo, Folha, Estadão, Correio, Estado de Minas e NYT.
- Cada candidato do Gmail usa uma página nova do navegador interno, como no Android.
- Corrigido o problema da v1.0.0 em que um timeout antigo podia atingir a candidata seguinte.
- Fluxo Gmail: `Apps Script -> até 5 Leia mais -> Ver página -> original_page -> download -> OCR -> melhor candidata`.
- Jornais do Gmail continuam **somente Gmail**, sem substituir por capa de internet.
- Valor Econômico e Washington Post usam a capa que estiver sendo exibida no link no momento, sem exigir a data selecionada.
- Valor continua sem busca aos sábados e domingos.
- Washington Post SPORTS continua rejeitado.
- Valor mantém PressReader como fallback depois do FrontPages.
- Revisão das candidatas e inserção manual continuam disponíveis.
- PDF, ordem dos jornais, capa padrão e otimização continuam preservados.

## Apps Script já configurado

O projeto já inclui como padrão:

`https://script.google.com/macros/s/AKfycbwO46cUIb0O--6_LUrysIjhCAlJJqjw0PRCuRLOTndiy4BkFZhNbXPQgA3rc9H8YC5l/exec`

## GitHub Releases

O workflow `.github/workflows/build-windows-portable.yml`:

1. compila no `windows-latest`;
2. inclui o OCR portátil;
3. cria o ZIP portable;
4. publica o resultado **diretamente em GitHub Releases** usando a versão de `version.txt`.

Release esperada: `windows-v1.0.1`.

## Teste recomendado

1. Rodar `ATUALIZAR CAPAS` para 24/08/2026.
2. Verificar se os jornais do Gmail começam a mudar de `Localizando páginas no Gmail...` mesmo enquanto Post/Valor ainda carregam.
3. Conferir O Globo/Folha/Estadão/Correio/Minas/NYT e navegar pelas candidatas recebidas.
4. Conferir Post e Valor separadamente.
5. Gerar o PDF e comparar com o Android.
