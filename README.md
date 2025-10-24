# ÉVORA Connect - Minimalist, Sophisticated Style

**Marketplace de Moda + Personal Shopping + Address Keeper + Integração WhatsApp**

## 🎯 O que é o ÉVORA?

ÉVORA é uma **rede social de cooperação** para compras internacionais (Orlando/EUA → Brasil), onde:

- **Clientes** compram produtos pelo WhatsApp
- **Personal Shoppers** fazem compras em lojas físicas
- **Keepers** armazenam e despacham produtos
- **Tudo acontece via WhatsApp** - zero instalação de apps

## 🚀 Quick Start

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/evora.git
cd evora

# Crie ambiente virtual
python -m venv .venv

# Ative o ambiente (Windows)
.venv\Scripts\activate

# Ative o ambiente (Linux/Mac)
source .venv/bin/activate

# Instale dependências
pip install -r requirements.txt

# Configure banco de dados
python manage.py migrate

# Crie superusuário
python manage.py createsuperuser

# Rode o servidor
python manage.py runserver
```

## 📁 Documentação

- **[Deploy Railway](DEPLOY_RAILWAY.md)** - 🚂 Deploy simplificado no Railway
- **[Setup Python](RAILWAY_PYTHON_SETUP.md)** - Configuração Python buildpack
- **[Integração WhatsApp](WHATSAPP_INTEGRATION.md)** - Como usar WhatsApp para vendas
- **[Guia de Migração](MIGRATION_GUIDE.md)** - Como migrar o banco de dados
- **[Resumo da Evolução](RESUMO_EVOLUCAO_EVORA.md)** - Histórico do projeto

## 🏗️ Arquitetura

- **Django 5.2.2** - Backend Python
- **PostgreSQL** - Banco de dados
- **Redis** - Cache e filas
- **Railway** - Deploy com Python buildpack
- **WhatsApp** - Interface de usuário (opcional)

## 📱 Comandos WhatsApp

```
/comprar 2x Victoria's Secret Body Splash
/entrega keeper
/pagar pix
/status
```

Ver documentação completa em [WHATSAPP_INTEGRATION.md](WHATSAPP_INTEGRATION.md)

## 💼 Funcionalidades Principais

### Para Clientes
- ✅ Comprar produtos pelo WhatsApp
- ✅ Escolher forma de entrega (keeper, correio, comprador)
- ✅ Pagar via PIX, cartão ou boleto
- ✅ Acompanhar pedidos em tempo real
- ✅ Rastrear encomendas

### Para Personal Shoppers
- ✅ Postar ofertas no grupo
- ✅ Receber pedidos automaticamente
- ✅ Marcar compras realizadas
- ✅ Informar viagens ao Brasil
- ✅ Receber comissões automaticamente

### Para Keepers
- ✅ Receber e armazenar pacotes
- ✅ Gerenciar slots de armazenamento
- ✅ Registrar postagens
- ✅ Agendar retiradas
- ✅ Receber taxas de guarda

## 🌐 Deploy

### Railway (Python Buildpack)

```bash
# Login
railway login

# Vincular projeto
railway link

# Deploy automático
git push origin main

# Ver logs
railway logs --tail
```

Ver guia completo: [DEPLOY_RAILWAY.md](DEPLOY_RAILWAY.md)

## 🔧 Comandos Úteis

```bash
# Fazer migrations
python manage.py makemigrations
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic

# Criar superusuário
python manage.py createsuperuser

# Atualizar requirements
pip freeze > requirements.txt
```

## 📊 Estrutura do Projeto

```
evora/
├── app_marketplace/          # App principal
│   ├── models.py            # Modelos (Cliente, Shopper, Keeper, etc.)
│   ├── admin.py             # Admin Django
│   ├── views.py             # Views
│   ├── urls.py              # URLs
│   ├── whatsapp_integration.py  # Parsers WhatsApp
│   └── templates/           # Templates HTML
├── setup/                   # Configurações Django
│   ├── settings.py          # Settings
│   └── urls.py              # URLs principais
├── MIGRATION_GUIDE.md       # Guia de migração
├── WHATSAPP_INTEGRATION.md  # Guia WhatsApp
├── RESUMO_EVOLUCAO_EVORA.md # Resumo do projeto
├── requirements.txt         # Dependências
└── manage.py               # Django CLI

```

## 📈 Estatísticas

- **22 Modelos Django** - Sistema completo
- **9 Novos Modelos** - Para Keeper e WhatsApp
- **+1.200 linhas** - De código novo
- **100% Python** - Backend
- **Zero Apps** - Tudo via WhatsApp

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📞 Suporte

- **Documentação**: [WHATSAPP_INTEGRATION.md](WHATSAPP_INTEGRATION.md)
- **Issues**: GitHub Issues
- **Email**: contato@evora.com

## 📝 Licença

Este projeto está sob a licença MIT.

---

**ÉVORA Connect** - *Where form becomes community. Where trust becomes network.*

✨ **Minimalist, Sophisticated Style** ✨
