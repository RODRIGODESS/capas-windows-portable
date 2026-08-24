# Principais Capas — Windows Portable v1.0.0

Primeira versão Windows Portable criada a partir da lógica funcional da versão Android v0.7.5.9.

## Objetivo
Levar para Windows o mesmo fluxo principal do app Android sem alterar o Apps Script que já está funcionando:

- data de busca selecionável;
- O Globo, Folha, Estadão, Correio Braziliense, Estado de Minas e New York Times via Gmail/Central Clipping;
- até 5 candidatas por jornal;
- revisão manual entre candidatas;
- inserção manual de capa e retorno à automática;
- Valor Econômico e Washington Post pelo FrontPages;
- Valor sem edição regular nos fins de semana;
- Washington Post rejeitando URL SPORTS;
- PDF `DDMMM - PRINCIPAIS CAPAS.pdf`;
- capa padrão como primeira página;
- capas completas, sem corte e sem deformação;
- PDF otimizado em JPEG 93%, até 2000 px de largura;
- abertura direta do PDF gerado.

## Interface Windows
Layout desktop em duas áreas:
- esquerda: lista dos 8 jornais, seleção, status e miniaturas;
- direita: prévia grande, navegação entre candidatas, inserção manual e restauração automática.

## Apps Script
O mesmo `/exec` do Android já está embutido:

`https://script.google.com/macros/s/AKfycbwO46cUIb0O--6_LUrysIjhCAlJJqjw0PRCuRLOTndiy4BkFZhNbXPQgA3rc9H8YC5l/exec`

O código atualmente usado também está em `google-apps-script/GmailCentralClipping.gs` apenas para referência. Não é necessário criar uma nova implantação para usar a versão Windows.

## GitHub Actions / Releases
O workflow `.github/workflows/build-windows-portable.yml`:
1. compila no `windows-latest`;
2. inclui o OCR Tesseract português/inglês dentro da pasta portátil;
3. cria `PrincipaisCapas-Windows-Portable-v1.0.0.zip`;
4. publica automaticamente o arquivo em **GitHub Releases**.

Não depende de Actions Artifacts para a entrega final.

## Como gerar
1. Crie/abra o repositório GitHub da versão Windows.
2. Envie **todo o conteúdo deste projeto**, inclusive a pasta `.github`.
3. Abra **Actions > Build Windows Portable + Release**.
4. Execute **Run workflow** (ou faça push na `main`).
5. Depois do build, abra **Releases** e baixe o ZIP portátil.

## Como usar
Extraia o ZIP da Release e execute:

`PrincipaisCapas.exe`

O programa grava cache/configuração em `data` ao lado do executável quando a pasta permite escrita. Os PDFs são salvos em:

`Downloads\Principais Capas`

## Observação desta primeira versão
A versão Windows usa Qt WebEngine para reproduzir o fluxo dinâmico `Leia mais -> Ver página -> original_page` e para obter as capas atuais de Valor/Post no FrontPages. O OCR é feito localmente pelo Tesseract incluído no pacote portátil.
