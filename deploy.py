#!/usr/bin/env python3
"""
Publica o conteudo deste repositorio nas paginas do WordPress em rcpb-fm.com.br.

Uso:
    python deploy.py
    python deploy.py --upload caminho/para/arquivo.png

O primeiro modo gera e publica as paginas listadas em PAGES. O segundo
envia um arquivo (imagem/video) pra Biblioteca de Midia do WordPress e
imprime a URL final, pronta pra colar em MEDIA_MAP.

Pede o usuario e a senha do wp-admin de forma interativa (a senha nao fica
visivel na tela e nao e' salva em nenhum arquivo). Tambem aceita as
variaveis de ambiente WP_USER / WP_PASS, se preferir nao digitar toda vez:

    WP_USER=usuario WP_PASS=senha python deploy.py

So usa a biblioteca padrao do Python (nao precisa `pip install` nada).

Ver README-DEPLOY.md para o contexto completo: por que o conteudo deste
repositorio estatico precisa ser publicado *dentro* de paginas WordPress
existentes, os ajustes que este script aplica no HTML e por que, e o que
ainda esta pendente.
"""

import getpass
import http.cookiejar
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

SITE_URL = "https://rcpb-fm.com.br"
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
USER_AGENT = "Mozilla/5.0 (deploy.py)"

# Modelo de pagina em branco (plugin Slider Revolution, ja instalado) — nao
# imprime o cabecalho/rodape do tema, so o post_content dentro de um
# <html>/<head>/<body> limpo. Ver README-DEPLOY.md.
TEMPLATE = "../public/views/revslider-page-template.php"

# Pagina deste repositorio -> pagina no WordPress.
PAGES = [
    {"file": "index.html", "id": 554, "url": "https://rcpb-fm.com.br/"},
    {"file": "sobre.html", "id": 967, "url": "https://rcpb-fm.com.br/quem-somos/"},
    {"file": "servicos.html", "id": 954, "url": "https://rcpb-fm.com.br/servicos-especializados/"},
    {"file": "contato.html", "id": 1019, "url": "https://rcpb-fm.com.br/contato/"},
    {"file": "estudo-tributario.html", "id": 7037, "url": "https://rcpb-fm.com.br/estudo-tributario/"},
]

# Caminho local (como aparece nos atributos src/href do HTML) -> URL real na
# Biblioteca de Midia do WordPress. Se adicionar/trocar uma imagem, faca o
# upload manual em Midia > Adicionar nova no wp-admin e adicione a URL
# retornada aqui.
MEDIA_MAP = {
    "img/fatima-logo.png": "https://rcpb-fm.com.br/wp-content/uploads/2026/08/fatima-logo.png",
    "img/fatima-logo-white.png": "https://rcpb-fm.com.br/wp-content/uploads/2026/08/fatima-logo-white.png",
    "img/fatima-retrato-hub.png": "https://rcpb-fm.com.br/wp-content/uploads/2026/08/fatima-retrato-hub.png",
    "img/rchub-logo-white.png": "https://rcpb-fm.com.br/wp-content/uploads/2026/08/rchub-logo-white.png",
    "img/rchub-logo.png": "https://rcpb-fm.com.br/wp-content/uploads/2026/08/rchub-logo.png",
    "img/localizacao-shopping-liv-mall.png": "https://rcpb-fm.com.br/wp-content/uploads/2026/08/localizacao-shopping-liv-mall.png",
    "video/endereco-rcpb.mp4": "https://rcpb-fm.com.br/wp-content/uploads/2026/08/endereco-rcpb.mp4",
}

# Link interno do repositorio -> URL real da pagina no WordPress.
LINK_MAP = {p["file"]: p["url"] for p in PAGES}


def read(rel_path):
    with open(os.path.join(REPO_DIR, rel_path), "r", encoding="utf-8") as f:
        return f.read()


def replace_attr(html, local_path, url):
    pattern = re.compile(r'(["\'])' + re.escape(local_path) + r'(["\'])')
    return pattern.sub(lambda m: m.group(1) + url + m.group(2), html)


def extract_body(html):
    m = re.search(r"<body>(.*?)</body>", html, re.DOTALL)
    if not m:
        raise ValueError("Nao encontrei <body> no HTML de origem")
    return m.group(1)


def extract_extra_style(html):
    # Blocos <style> especificos de cada pagina, que no HTML de origem ficam
    # dentro do <head> (ex.: .mvv-grid em sobre.html, .servicos-grid em
    # servicos.html). Precisam ser movidos pro corpo, ja que so aproveitamos
    # o <body> do arquivo original.
    head_match = re.search(r"<head>(.*?)</head>", html, re.DOTALL)
    head = head_match.group(1) if head_match else ""
    styles = re.findall(r"<style>.*?</style>", head, re.DOTALL)
    return "\n".join(styles)


def build_page(file_name):
    html = read(file_name)
    for local_path, url in MEDIA_MAP.items():
        html = replace_attr(html, local_path, url)
    for local_path, url in LINK_MAP.items():
        html = replace_attr(html, local_path, url)

    extra_style = extract_extra_style(html)
    body = extract_body(html)
    # remove a tag <script src="js/main.js"> — o conteudo do main.js e' inlinado abaixo
    body = re.sub(r'\s*<script src="js/main\.js"></script>\s*', "\n", body)

    css = read("css/style.css")
    js = read("js/main.js")

    # FIX 1 — scroll travado: o tema (Massive Dynamic) carrega globalmente um
    # script de "smooth scroll" que substitui a rolagem nativa por uma
    # versao animada via JS, deixando o scroll lento/travado. Nao temos
    # acesso pra remover esse script do tema (edicao de arquivo de tema
    # bloqueada nessa hospedagem), entao neutralizamos os listeners dele em
    # fase de captura (roda antes dos listeners do tema, que usam a fase
    # padrao de bubble), sem chamar preventDefault — a rolagem nativa do
    # navegador continua funcionando normal.
    scroll_fix = (
        "(function () {\n"
        "  var stop = function (e) { e.stopImmediatePropagation(); };\n"
        "  ['wheel', 'mousewheel', 'DOMMouseScroll', 'touchstart', 'touchmove'].forEach(function (type) {\n"
        "    document.addEventListener(type, stop, true);\n"
        "  });\n"
        "})();\n"
    )

    # FIX 2 — rodape invisivel: o tema tem uma rotina JS
    # (pixflow_show_footer / pixflow_footerPosition) que espera elementos
    # <main>/<header> proprios do tema pra revelar o rodape (ele comeca
    # oculto e um script depende dessa estrutura pra mostra-lo). Como nossas
    # paginas nao tem essa estrutura, esse script provavelmente quebra antes
    # de revelar o footer. Forcamos a visibilidade aqui, independente da
    # causa exata da quebra.
    footer_fix = (
        "footer{visibility:visible !important;opacity:1 !important;"
        "display:block !important;position:static !important;}"
    )

    # FIX 3 — barra de credito branca: um plugin injeta uma div com id fixo
    # (#xf-779-a510f8) no rodape do site inteiro, que tenta detectar via JS
    # a cor de fundo do <footer> pra combinar com ele. Essa deteccao falha
    # nas nossas paginas e a barra fica branca, criando um "gap" visual.
    # Forcamos a cor certa via !important, que vence a atribuicao inline que
    # o script da barra faz depois.
    credit_bar_fix = (
        "#xf-779-a510f8{background-color:var(--black-soft) !important;"
        "color:var(--black-soft) !important;}"
        "#xf-779-a510f8 a{color:var(--black-soft) !important;}"
    )

    out = "<style>\n" + css + "\n" + footer_fix + "\n" + credit_bar_fix + "\n</style>\n"
    if extra_style:
        out += extra_style + "\n"
    out += body
    out += "\n<script>\n" + scroll_fix + "\n" + js + "\n</script>\n"
    return out


def build_all_pages():
    print("==> Gerando HTML de cada pagina")
    result = {}
    for page in PAGES:
        html = build_page(page["file"])
        result[page["id"]] = html
        print("    %-24s %6d bytes" % (page["file"], len(html.encode("utf-8"))))
    return result


def make_opener():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def request(opener, url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET")
    req.add_header("User-Agent", USER_AGENT)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    return opener.open(req, timeout=30)


def login(opener, user, password):
    print("==> Fazendo login em %s/wp-login.php" % SITE_URL)
    # prime o cookie de teste do WordPress
    request(opener, SITE_URL + "/wp-login.php").read()

    form = urllib.parse.urlencode({
        "log": user,
        "pwd": password,
        "wp-submit": "Log In",
        "redirect_to": SITE_URL + "/wp-admin/",
        "testcookie": "1",
    }).encode("utf-8")
    request(opener, SITE_URL + "/wp-login.php", data=form).read()


def get_rest_nonce(opener):
    print("==> Obtendo nonce da API REST")
    body = request(opener, SITE_URL + "/wp-admin/").read().decode("utf-8", "ignore")
    m = re.search(r'wpApiSettings\s*=\s*\{[^}]*"nonce":"([a-f0-9]+)"', body)
    if not m:
        raise RuntimeError(
            "Nao consegui obter o nonce da API REST — o login provavelmente falhou "
            "(usuario/senha errados?)."
        )
    nonce = m.group(1)
    print("    nonce: %s" % nonce)
    return nonce


def publish_page(opener, nonce, page_id, content):
    payload = json.dumps({"content": content, "template": TEMPLATE}).encode("utf-8")
    url = "%s/wp-json/wp/v2/pages/%d" % (SITE_URL, page_id)
    try:
        resp = request(opener, url, data=payload, headers={
            "X-WP-Nonce": nonce,
            "Content-Type": "application/json; charset=utf-8",
        })
        return resp.status
    except urllib.error.HTTPError as e:
        print("    erro: %s" % e.read().decode("utf-8", "ignore")[:300])
        return e.code


def build_multipart(fields, files):
    """Monta um corpo multipart/form-data (upload de arquivo) so com stdlib."""
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append(("--%s" % boundary).encode())
        parts.append(('Content-Disposition: form-data; name="%s"' % name).encode())
        parts.append(b"")
        parts.append(str(value).encode("utf-8"))
    for name, (filename, content, mime) in files.items():
        parts.append(("--%s" % boundary).encode())
        parts.append(
            ('Content-Disposition: form-data; name="%s"; filename="%s"' % (name, filename)).encode()
        )
        parts.append(("Content-Type: %s" % mime).encode())
        parts.append(b"")
        parts.append(content)
    parts.append(("--%s--" % boundary).encode())
    parts.append(b"")
    body = b"\r\n".join(parts)
    content_type = "multipart/form-data; boundary=%s" % boundary
    return content_type, body


def get_credentials():
    user = os.environ.get("WP_USER") or input("Usuario do wp-admin: ")
    password = os.environ.get("WP_PASS") or getpass.getpass("Senha do wp-admin: ")
    return user, password


def upload_media(opener, file_path):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(file_path)

    print("==> Obtendo nonce de upload de midia")
    body = request(opener, SITE_URL + "/wp-admin/media-new.php").read().decode("utf-8", "ignore")
    m = re.search(r'name="_wpnonce" value="([a-f0-9]+)"', body)
    if not m:
        raise RuntimeError(
            "Nao consegui obter o nonce de upload — o login provavelmente falhou."
        )
    nonce = m.group(1)

    filename = os.path.basename(file_path)
    mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    with open(file_path, "rb") as f:
        content = f.read()

    print("==> Enviando %s (%d bytes, %s)" % (filename, len(content), mime))
    content_type, payload = build_multipart(
        {"action": "upload-attachment", "_wpnonce": nonce, "name": filename},
        {"async-upload": (filename, content, mime)},
    )
    resp = request(
        opener,
        SITE_URL + "/wp-admin/async-upload.php",
        data=payload,
        headers={"Content-Type": content_type},
    )
    result = json.loads(resp.read().decode("utf-8"))
    if not result.get("success"):
        raise RuntimeError("Falha no upload: %s" % result)

    url = result["data"]["url"]
    print("    URL: %s" % url)
    print('    Adicione em MEDIA_MAP: "img/%s": "%s",' % (filename, url))
    return url


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--upload":
        if len(sys.argv) < 3:
            print("Uso: python deploy.py --upload caminho/para/arquivo.png", file=sys.stderr)
            sys.exit(1)
        user, password = get_credentials()
        opener = make_opener()
        login(opener, user, password)
        upload_media(opener, sys.argv[2])
        return

    user, password = get_credentials()

    pages_content = build_all_pages()

    opener = make_opener()
    login(opener, user, password)
    nonce = get_rest_nonce(opener)

    for page in PAGES:
        print("==> Publicando %-24s (id %d)" % (page["file"], page["id"]))
        status = publish_page(opener, nonce, page["id"], pages_content[page["id"]])
        print("    http:%s  %s" % (status, page["url"]))

    print("==> Pronto. Confira as paginas no ar.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
