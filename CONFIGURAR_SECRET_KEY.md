# 🔐 Configurar SECRET_KEY no Railway

## 📝 SECRET_KEY Gerado

Execute este comando para gerar uma nova chave:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 🚀 Como Configurar no Railway

### Opção 1: Via Dashboard Railway (Recomendado)

1. Acesse o dashboard do Railway: https://railway.app
2. Selecione seu projeto
3. Selecione o serviço Django
4. Vá em **Variables**
5. Clique em **+ New Variable**
6. Adicione:
   - **Name**: `SECRET_KEY`
   - **Value**: Cole a chave gerada
7. Clique em **Add**

### Opção 2: Via CLI Railway

```bash
# Gerar chave
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Configurar no Railway (substitua YOUR_SECRET_KEY pela chave gerada)
railway variables set SECRET_KEY="YOUR_SECRET_KEY"
```

### Opção 3: Via arquivo .env (apenas desenvolvimento local)

Crie um arquivo `.env` na raiz do projeto:

```bash
SECRET_KEY=sua-chave-gerada-aqui
```

⚠️ **NUNCA** commite o arquivo `.env` no Git!

## ✅ Verificar se está configurado

```bash
# Via CLI
railway variables | grep SECRET_KEY

# Ou verificar no dashboard Railway
```

## 🔒 Importante

- ✅ **Use uma chave diferente para cada ambiente** (desenvolvimento, produção)
- ✅ **Nunca compartilhe a chave** publicamente
- ✅ **Regenere a chave** se suspeitar que foi comprometida
- ❌ **Nunca** commite SECRET_KEY no código

## 📝 Nota

O `settings.py` já está configurado para usar a variável de ambiente:

```python
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-8j^$b4kv512@8mlg=koq)5iu8#fpqz#=ot8ost*)g^eyexvq!b')
```

Se `SECRET_KEY` não estiver configurado no Railway, Django usará o fallback (não recomendado para produção).

---

**Próximo passo**: Após configurar, faça um novo deploy para aplicar as mudanças.

