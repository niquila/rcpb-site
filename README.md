# Site RCPB Contabilidade

Site institucional estático (HTML/CSS/JS puro — sem framework, sem build step).

## Estrutura

```
/
├── index.html              → Home
├── sobre.html               → Quem somos (missão, visão, valores, história)
├── servicos.html             → Serviços (Auditoria, Societário, Consultoria Financeira, Pessoal, Contábil e Fiscal)
├── estudo-tributario.html    → Landing page do produto Estudo Tributário
├── contato.html              → Contato
├── css/
│   └── style.css             → Estilo compartilhado (cores, tipografia, componentes)
├── js/
│   └── main.js                → Menu mobile, FAQ (acordeão), formulários
└── img/
    └── fatima-retrato-hub.png → Retrato institucional
```

## Como publicar

Como é um site 100% estático, pode ser hospedado em qualquer serviço de hospedagem estática, por exemplo:

- **Vercel** ou **Netlify** — arraste a pasta inteira no painel, ou conecte a um repositório Git
- **GitHub Pages** — suba os arquivos pra um repositório e ative o Pages nas configurações
- **Hospedagem tradicional (cPanel/FTP)** — envie os arquivos via FTP pra pasta `public_html` (ou equivalente) do domínio

**Domínio sugerido:** subdomínio de `rcpb-fm.com.br` (ex: `estudotributario.rcpb-fm.com.br` para a landing, ou substituir o site institucional atual pelo `rcpb-fm.com.br` completo).

## O que falta configurar antes de ir ao ar

1. **Formulários** — já estão conectados ao webhook da AcqOps (`https://www.acqops.com.br/webhooks/landing-page?ref=3f023b087ea70368`), definido em `js/main.js` na constante `WEBHOOK_URL`. Cada envio manda um JSON com todos os campos do formulário (por `id`) mais `origem`, `pagina`, `url` e `enviado_em`. **Importante testar após publicar:** o envio usa `fetch` direto do navegador — se o servidor da AcqOps não liberar CORS para o domínio onde o site for hospedado, o envio pode falhar silenciosamente (cai no `catch`, mostra alerta "Não foi possível enviar agora"). Testar um envio de teste assim que o site estiver no ar e confirmar com a AcqOps se o domínio final está liberado.
2. **Pixel do Google Ads / Meta Ads** — não está instalado. Para rastrear conversões da campanha, adicionar o script de rastreamento no `<head>` de cada página (ou só na `estudo-tributario.html`, se for a landing da campanha).
3. **Domínio e SSL** — depende de onde for hospedado.
4. **WhatsApp** — os links já apontam para `https://wa.me/5583996214000` (número do Geraldo, usado no formulário Diagnóstico RCPB). Confirmar se é esse o número correto para todos os contextos do site.

## Identidade visual

- Vermelho: `#C0392B`
- Preto: `#111111`
- Branco: `#FFFFFF`
- Fonte: Arial (em todo o site)
- Variáveis de cor centralizadas em `css/style.css` (`:root`) — para trocar uma cor em todo o site, basta editar ali.

## Observação sobre a página do Estudo Tributário

Essa página reaproveita a copy (promessa, oferta, garantia, objeções) já validada com a especialista em Reforma Tributária responsável pela RCPB. Qualquer alteração de texto nessa página deve manter:
- O nome do produto: **Estudo Tributário** (não confundir com "Planejamento Tributário", que é outro produto)
- O nome do entregável: **Raio-X da Reforma Tributária**
- A distinção entre o diagnóstico (via questionário) e a consultoria de 15 minutos (bônus, não etapa obrigatória)
