// ===========================================================
// RCPB Contabilidade — script compartilhado
// ===========================================================

// Menu mobile
document.addEventListener('DOMContentLoaded', function () {
  var toggle = document.querySelector('.menu-toggle');
  var mobileMenu = document.querySelector('.mobile-menu');
  if (toggle && mobileMenu) {
    toggle.addEventListener('click', function () {
      mobileMenu.classList.toggle('open');
    });
  }

  // FAQ accordion (usado em estudo-tributario.html)
  document.querySelectorAll('.faq-item').forEach(function (item) {
    var q = item.querySelector('.faq-q');
    var a = item.querySelector('.faq-a');
    if (!q || !a) return;
    q.addEventListener('click', function () {
      var isOpen = item.classList.contains('open');
      document.querySelectorAll('.faq-item.open').forEach(function (open) {
        if (open !== item) {
          open.classList.remove('open');
          open.querySelector('.faq-a').style.maxHeight = null;
        }
      });
      if (isOpen) {
        item.classList.remove('open');
        a.style.maxHeight = null;
      } else {
        item.classList.add('open');
        a.style.maxHeight = a.scrollHeight + 'px';
      }
    });
  });

  // Formulário de contato / diagnóstico — envio real via webhook AcqOps
  var WEBHOOK_URL = 'https://www.acqops.com.br/webhooks/landing-page?ref=3f023b087ea70368';

  var forms = document.querySelectorAll('form[data-form]');
  forms.forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = form.querySelector('button[type="submit"]');
      var originalText = btn ? btn.textContent : '';
      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Enviando...';
      }

      // monta o payload a partir de todos os campos do formulário (por id)
      var payload = {
        origem: 'site-rcpb',
        pagina: document.title,
        url: window.location.href,
        enviado_em: new Date().toISOString()
      };
      form.querySelectorAll('input, select, textarea').forEach(function (field) {
        if (field.id) payload[field.id] = field.value;
      });

      fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
        .then(function (response) {
          if (!response.ok) throw new Error('Resposta não OK: ' + response.status);
          if (btn) btn.textContent = 'Recebemos seus dados ✓';
          form.reset();
        })
        .catch(function (error) {
          console.error('Erro ao enviar formulário para o webhook:', error);
          if (btn) {
            btn.disabled = false;
            btn.textContent = originalText;
          }
          alert('Não foi possível enviar agora. Tente novamente ou fale pelo WhatsApp.');
        });
    });
  });
});
