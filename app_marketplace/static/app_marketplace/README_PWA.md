# PWA - Progressive Web App

Este diretório contém todos os arquivos necessários para o PWA do ÉVORA Connect.

## Arquivos

- `manifest.json` - Manifesto do PWA com informações do app
- `sw.js` - Service Worker para cache offline
- `pwa-install.js` - Script para instalação do PWA
- `icons/` - Ícones do aplicativo em vários tamanhos

## Ícones Necessários

Os ícones devem ser colocados no diretório `icons/` com os seguintes tamanhos:

- `icon-72x72.png`
- `icon-96x96.png`
- `icon-128x128.png`
- `icon-144x144.png`
- `icon-152x152.png`
- `icon-192x192.png`
- `icon-384x384.png`
- `icon-512x512.png`

### Gerar Ícones

**AUTOMÁTICO (Recomendado):**

O projeto inclui um script Python que gera todos os ícones automaticamente:

```bash
python app_marketplace/static/app_marketplace/generate_icons.py
```

O script:
- ✅ Detecta automaticamente se existe um logo (LOGO.jpeg, logo.png, etc.) na pasta `icons/`
- ✅ Gera todos os tamanhos necessários (72x72 até 512x512)
- ✅ Se não houver logo, cria ícones programaticamente com o tema do ÉVORA
- ✅ Requer apenas `pip install Pillow`

**MANUAL (Alternativa):**

Você também pode usar ferramentas online como:
- [PWA Asset Generator](https://github.com/onderceylan/pwa-asset-generator)
- [RealFaviconGenerator](https://realfavicongenerator.net/)
- [PWA Builder](https://www.pwabuilder.com/imageGenerator)

Ou criar manualmente a partir de um logo/ícone base (recomendado: 512x512px ou maior).

## Como usar

### Instalação

1. Acesse o site no navegador (Chrome, Edge, Safari)
2. O navegador mostrará automaticamente um prompt para instalar
3. Ou clique no botão "📱 Instalar App" que aparece no canto inferior direito

### Funcionalidades

- ✅ Instalação como app nativo
- ✅ Funciona offline (com cache)
- ✅ Ícone na tela inicial
- ✅ Tema personalizado (azul #0d6efd)
- ✅ Suporte para iOS e Android

## Testando

1. Abra o DevTools (F12)
2. Vá para a aba "Application" (Chrome) ou "Manifest" (Firefox)
3. Verifique:
   - Service Worker está registrado
   - Manifest está carregado
   - Cache está funcionando

## Notas

- O Service Worker usa estratégia "Network First" com fallback para cache
- Os ícones devem ser PNG com fundo transparente ou sólido
- O tema usa as cores do Bootstrap (#0d6efd para azul primário e #212529 para fundo escuro)

## Atualização do Cache

Quando atualizar o PWA, altere a versão do cache em `sw.js`:
```javascript
const CACHE_NAME = 'evora-connect-v2'; // Incremente a versão
```

Isso força a atualização do cache para todos os usuários.

