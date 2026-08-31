# Como publicar este repositório em rcpb-fm.com.br

Este repositório é um site estático (HTML/CSS/JS puro), mas o domínio
`rcpb-fm.com.br` roda WordPress (tema **Massive Dynamic**, construtor
**WPBakery**). Este documento explica como o conteúdo daqui chega até lá e
como qualquer pessoa da equipe pode repetir o processo.

## Por que não é só "subir os arquivos"

A forma mais simples seria subir os arquivos deste repositório direto na
raiz do site (via FTP/SFTP ou um plugin de gerenciador de arquivos). Isso
**não foi possível** com o acesso disponível hoje (só login de administrador
no wp-admin):

- **Instalação de plugins está bloqueada** nessa hospedagem — tentamos
  instalar o WP File Manager (via wordpress.org e via upload manual do
  `.zip`) e as duas vias foram recusadas pelo próprio WordPress
  ("Sorry, you are not allowed to install plugins on this site").
- **Edição de arquivo do tema/plugin também não funciona** — o Editor de
  Temas do wp-admin abre e permite editar, mas ao salvar, o WordPress tenta
  fazer uma requisição para si mesmo pra checar se o PHP novo não quebra o
  site (proteção nativa desde a versão 5.2). Nesse servidor essa
  autoverificação falha (provavelmente algo no proxy/firewall bloqueando o
  site de se acessar), e a alteração é **desfeita automaticamente** — com
  segurança, mas também sem funcionar.
- O site está hospedado na **Oracle Cloud Infrastructure** (IP com ASN da
  Oracle Corporation), não numa hospedagem compartilhada com painel/FTP
  pronto — então não há um "cPanel" óbvio pra pedir acesso, seria preciso
  achar quem administra essa VM.

Dado isso, a solução encontrada foi **recriar o conteúdo dentro do próprio
WordPress**, usando só a API REST (que funciona normalmente com login de
administrador) e um recurso que já existia no site: um modelo de página em
branco.

## Como funciona

```
rcpb-site/ (este repo)                                    WordPress (rcpb-fm.com.br)
├─ index.html          ──┐                                 ┌─ Home (id 554)
├─ sobre.html            │        python deploy.py          ├─ Quem Somos (id 967)
├─ servicos.html         ├──►   (le os .html, troca     ──► ├─ Serviços Especializados (id 954)
├─ contato.html          │      imagens/links pelas          ├─ Contato (id 1019)
├─ estudo-tributario.html│      URLs reais do WP,           └─ Estudo Tributário (id 7037)
├─ css/style.css         │      aplica os fixes e
└─ js/main.js          ──┘      publica via API REST)
```

**`deploy.py`** é um único script Python (só biblioteca padrão, não precisa
`pip install` nada) que faz tudo isso, nessa ordem:

1. Lê cada página deste repositório e gera uma versão pronta para o
   WordPress: troca `img/...` e `video/...` pelas URLs reais da Biblioteca
   de Mídia do WP, troca os links internos (`sobre.html` etc.) pelas URLs
   reais das páginas no WP, extrai só o `<body>`, e inlina o `css/style.css`
   e o `js/main.js` diretamente no conteúdo (não dá pra servir arquivos
   `.css`/`.js` separados sem plugin — ver seção seguinte).
2. Cada página do WordPress usa o modelo **"Slider Revolution Blank
   Template"** (vem do plugin Slider Revolution, já instalado) — um modelo
   que não imprime o cabeçalho/rodapé do tema, só `<?php the_content(); ?>`
   dentro de um `<html>/<head>/<body>` limpo. Isso permite que o HTML deste
   repositório (que já tem seu próprio `<header>`, `<nav>` e `<footer>`)
   controle a página inteira, sem duplicar o header/footer do tema.
3. Faz login no wp-admin, pega um nonce da API REST, e envia o conteúdo
   gerado para cada página via `POST /wp-json/wp/v2/pages/{id}` —
   substituindo o `post_content` (que no WordPress normal seria os
   shortcodes do WPBakery) pelo nosso HTML puro.

## Mapeamento de páginas

| Página deste repo         | Página no WordPress          | id WP  | URL                                              |
|----------------------------|-------------------------------|--------|---------------------------------------------------|
| `index.html`                | Home                           | 554    | https://rcpb-fm.com.br/                            |
| `sobre.html`                 | Quem Somos                     | 967    | https://rcpb-fm.com.br/quem-somos/                 |
| `servicos.html`              | Serviços Especializados         | 954    | https://rcpb-fm.com.br/servicos-especializados/    |
| `contato.html`               | Contato                         | 1019   | https://rcpb-fm.com.br/contato/                    |
| `estudo-tributario.html`      | Estudo Tributário (página nova) | 7037   | https://rcpb-fm.com.br/estudo-tributario/          |

Esse mapeamento vive no topo de `deploy.py` (lista `PAGES`).

Outras páginas que já existiam no WordPress (Responsabilidades, Práticas de
Gestão, Inovação, Blog) foram **deixadas como estavam**, por decisão do
cliente — este repositório não tem conteúdo equivalente pra elas.

## Imagens e vídeo

As imagens (`img/*.png`) e o vídeo (`video/endereco-rcpb.mp4`) foram
enviados para a Biblioteca de Mídia do WordPress, porque não dá pra
referenciar arquivos deste repositório diretamente — eles precisam estar
hospedados em algum lugar acessível pelo domínio. As URLs resultantes estão
mapeadas em `MEDIA_MAP`, no topo de `deploy.py`.

**Se adicionar ou trocar uma imagem/vídeo:**

```bash
python deploy.py --upload img/nova-imagem.png
```

Isso envia o arquivo pra Biblioteca de Mídia e imprime a URL final, já no
formato pronto pra colar em `MEDIA_MAP` (`deploy.py`). Copie a linha
sugerida, adicione em `MEDIA_MAP`, e use o caminho normalmente no HTML.

(Também dá pra fazer esse upload manualmente pelo wp-admin em Mídia >
Adicionar nova, copiando a URL de lá — o resultado é o mesmo.)

## Como publicar uma alteração

Pré-requisito: **Python 3** (nada além disso — o script só usa biblioteca
padrão) e um usuário WordPress com papel de **Administrador**.

```bash
# 1. Edite os arquivos normalmente (index.html, css/style.css, etc.)

# 2. Rode o deploy
python deploy.py
```

O script pergunta o usuário e a senha do wp-admin na hora (a senha não
aparece na tela e não é salva em nenhum arquivo). Se preferir não digitar
toda vez, pode passar por variável de ambiente:

```bash
WP_USER=seu_usuario WP_PASS=sua_senha python deploy.py
```

No Windows, isso funciona tanto no **PowerShell** quanto no **Git Bash** —
só muda a sintaxe da variável de ambiente:

```powershell
# PowerShell
$env:WP_USER = "seu_usuario"; $env:WP_PASS = "sua_senha"; python deploy.py
```

```bash
# Git Bash
WP_USER=seu_usuario WP_PASS=sua_senha python deploy.py
```

Nunca commite usuário/senha em nenhum arquivo do repositório.

## Ajustes que o `deploy.py` aplica automaticamente (e por quê)

Essas correções existem por causa de comportamentos do tema/plugins do
WordPress por baixo — **não remova sem entender o motivo**, ou os problemas
originais voltam:

1. **Scroll travado** — o tema carrega globalmente um script de "smooth
   scroll" que substitui a rolagem nativa do navegador por uma versão
   animada via JS, deixando o scroll visivelmente lento. `deploy.py` injeta
   um pequeno script que intercepta os eventos de wheel/touch em fase de
   captura (roda antes do script do tema) e impede que ele receba o evento,
   sem chamar `preventDefault` — a rolagem nativa continua funcionando.
2. **Rodapé invisível** — o tema tem uma rotina (`pixflow_show_footer` /
   `pixflow_footerPosition`) que só revela o `<footer>` via JS depois de
   calcular posições usando elementos próprios do tema (`<main>`,
   `<header>` com certas classes) que nossas páginas não têm. Esse script
   provavelmente quebra no meio da execução antes de revelar o rodapé,
   deixando-o com `visibility:hidden` mesmo com o conteúdo presente no HTML.
   `deploy.py` força `visibility:visible` (com `!important`) pra contornar.
3. **Barra de crédito branca no fim da página** — um plugin injeta uma
   `<div id="xf-779-a510f8">` no rodapé de todas as páginas do site, que
   tenta detectar via JS a cor de fundo do `<footer>` pra combinar com ele.
   Essa detecção falha nas nossas páginas e a barra fica branca, criando um
   "gap" visual. `deploy.py` força a cor certa nessa div específica via
   `!important` (que vence a atribuição inline que o script da barra faz
   depois).

## Se aparecer outro problema visual parecido (script do tema quebrando)

Os 3 ajustes acima existem porque encontramos e testamos esses problemas
especificamente nas páginas já publicadas — **não tem como blindar
preventivamente** contra todo script do tema (`custom.min.js` e outros
carregam bastante coisa que assume elementos/classes próprios do tema,
tipo `.layout-container`, `header.top`, `.business`, etc., que nossas
páginas não têm). Chegamos a avaliar adicionar um `<main>` vazio pra evitar
esse tipo de quebra de forma mais geral, mas o próprio CSS do tema tem
regras genéricas pra `<main>` (`margin-top:110px`, `width:90% !important`
em certas larguras) que recriariam um gap parecido — não é um fix de graça.

Então o processo, quando aparecer algo estranho numa página nova ou depois
de uma alteração:

1. Tira um print (ou descreve) do que está errado.
2. Isso é investigado igual aos 3 casos acima: geralmente é um script do
   tema fazendo alguma suposição sobre a estrutura da página que não é
   verdadeira aqui.
3. A correção vira mais uma entrada dentro da função `build_page()` em
   `deploy.py` (CSS/JS injetado junto do conteúdo, do mesmo jeito que os
   3 fixes existentes), documentada com um comentário explicando a causa —
   pra não virar um "remendo misterioso" pra quem mexer nisso depois.

## O que ainda está pendente

1. **Formulários de contato** (`Enviar mensagem` / `Quero meu Raio-X
   Tributário`) enviam para um webhook externo (`acqops.com.br`, definido em
   `js/main.js`). O site tem uma política de segurança (CSP) que **bloqueia
   `fetch()` para qualquer domínio fora de uma lista específica**, e
   `acqops.com.br` não está nela — o envio provavelmente falha
   silenciosamente. Não há como ajustar isso só pelo wp-admin (não
   conseguimos editar o `functions.php` nem a config do servidor onde essa
   CSP é definida). Duas saídas possíveis:
   - Pedir para quem administra o servidor/CSP liberar `acqops.com.br` em
     `connect-src` e `form-action`.
   - Trocar o formulário por **Contact Form 7** (já instalado no site), que
     envia via `admin-ajax.php` (mesma origem, não é bloqueado pela CSP),
     mas muda para onde os leads chegam (e-mail em vez do webhook/CRM).
2. **Favicon e `<meta name="description">`** não são aplicados nessas
   páginas — o modelo em branco só controla o `<body>`, não o `<head>`
   (que é gerado pelo `wp_head()` do WordPress).
3. Instalação de plugin e edição de arquivo de tema continuam bloqueadas
   nessa hospedagem (ver seção acima) — qualquer solução futura que dependa
   disso vai esbarrar no mesmo problema, a menos que alguém consiga acesso
   real ao servidor (SSH/FTP) ou resolva o motivo da autoverificação do
   WordPress falhar.
