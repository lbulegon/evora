# ⚡ Teste Rápido - Configuração OpenMind AI

## 🧪 Testes Rápidos

### 1. Testar Servidor SinapUm (Health Check)

```bash
curl http://69.169.102.84:8000/health
```

**Esperado:** `{"status": "healthy", "service": "OpenMind AI Server"}`

---

### 2. Verificar Variáveis no ÉVORA

```bash
python manage.py shell
```

Depois execute no shell:
```python
from django.conf import settings
print("✅ AI_SERVICE:", settings.AI_SERVICE)
print("✅ OPENMIND_AI_URL:", settings.OPENMIND_AI_URL)
print("✅ OPENMIND_AI_KEY:", "Configurado" if settings.OPENMIND_AI_KEY else "❌ NÃO configurado")
print("✅ OPENMIND_ORG_MODEL:", settings.OPENMIND_ORG_MODEL)
```

---

### 3. Testar Análise de Imagem no ÉVORA

1. Iniciar servidor:
   ```bash
   python manage.py runserver
   ```

2. Acessar: http://localhost:8000/products/cadastrar-por-foto/

3. Tirar/fazer upload de foto de produto

4. Verificar se analisa e preenche os dados

---

### 4. Testar no Railway

1. Acessar: https://evora-product.up.railway.app/products/cadastrar-por-foto/

2. Fazer upload de foto

3. Verificar análise

---

## ✅ Pronto para Testar!

**Qual teste você quer fazer primeiro?** 🚀
