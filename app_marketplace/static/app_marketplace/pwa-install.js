// Script para instalação do PWA
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  // Previne o prompt automático
  e.preventDefault();
  // Guarda o evento para usar depois
  deferredPrompt = e;
  // Mostra o botão de instalação
  showInstallButton();
});

function showInstallButton() {
  // Cria ou mostra o botão de instalação
  let installButton = document.getElementById('pwa-install-button');
  
  if (!installButton) {
    installButton = document.createElement('button');
    installButton.id = 'pwa-install-button';
    installButton.innerHTML = '📱 Instalar App';
    installButton.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #0d6efd;
      color: #ffffff;
      border: none;
      padding: 12px 20px;
      border-radius: 25px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 4px 15px rgba(13, 110, 253, 0.4);
      z-index: 1000;
      font-size: 14px;
      transition: all 0.3s;
    `;
    
    installButton.addEventListener('mouseenter', () => {
      installButton.style.transform = 'translateY(-2px)';
      installButton.style.boxShadow = '0 6px 20px rgba(13, 110, 253, 0.5)';
    });
    
    installButton.addEventListener('mouseleave', () => {
      installButton.style.transform = 'translateY(0)';
      installButton.style.boxShadow = '0 4px 15px rgba(13, 110, 253, 0.4)';
    });
    
    installButton.addEventListener('click', installPWA);
    document.body.appendChild(installButton);
  }
  
  installButton.style.display = 'block';
}

function installPWA() {
  if (!deferredPrompt) {
    return;
  }
  
  // Mostra o prompt de instalação
  deferredPrompt.prompt();
  
  // Aguarda a resposta do usuário
  deferredPrompt.userChoice.then((choiceResult) => {
    if (choiceResult.outcome === 'accepted') {
      console.log('Usuário aceitou a instalação');
    } else {
      console.log('Usuário rejeitou a instalação');
    }
    
    // Limpa o prompt
    deferredPrompt = null;
    
    // Esconde o botão
    const installButton = document.getElementById('pwa-install-button');
    if (installButton) {
      installButton.style.display = 'none';
    }
  });
}

// Detecta se o app já está instalado
window.addEventListener('appinstalled', () => {
  console.log('PWA instalado com sucesso');
  const installButton = document.getElementById('pwa-install-button');
  if (installButton) {
    installButton.style.display = 'none';
  }
});

