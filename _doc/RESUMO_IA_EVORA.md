# Resumo da Implementação de IA no ÉVORA Connect

Este documento resume o que já existe de IA no ÉVORA e o plano para migrar para OpenMind AI.

---

## 📋 O Que Já Existe

### 1. Módulo de Extração de Produtos (`app_marketplace/ai_product_extractor.py`)

**Funcionalidade:**
- Analisa imagens de produtos usando OpenAI Vision API (GPT-4o)
- Extrai informações de rótulos/embalagens
- Formata dados no padrão JSON ÉVORA

**Funções Principais:**
- `extract_product_data_from_image(image_file)` - Extrai dados da imagem
- `format_evora_json(extracted_data, image_url)` - Formata no padrão ÉVORA
- `generate_sku_interno(nome_produto, marca)` - Gera SKU no padrão EVR-XXX-XXX

**Uso:**
- Usado em `product_photo_views.py` para análise de fotos de produtos
- Endpoint: `/api/produtos/detectar_por_foto/`

### 2. Integração com Foto de Produtos

**Arquivo:** `app_marketplace/product_photo_views.py`

**Fluxo:**
1. Usuário tira foto do produto
2. Imagem é enviada para `/api/produtos/detectar_por_foto/`
3. `extract_product_data_from_image()` é chamado
4. OpenAI analisa a imagem
5. Dados são formatados no padrão JSON ÉVORA
6. Formulário é pré-preenchido com os dados

### 3. Modelo no Banco de Dados

**Modelo:** `OpenAIKey` (`app_marketplace/models.py`)
- Armazena chaves da OpenAI
- Não está sendo usado atualmente (usa variável de ambiente)

### 4. Comando de Teste

**Arquivo:** `app_marketplace/management/commands/openiaset.py`
- Comando Django para testar conexão com OpenAI
- Envia perguntas para GPT-3.5-turbo

---

## 🎯 Estratégia: Migrar para OpenMind AI

### Objetivo
Substituir completamente a OpenAI pelo servidor OpenMind AI próprio hospedado no SinapUm.

---

## 🔄 Plano de Migração

### Fase 1: Adaptar Módulo Atual (Foco Agora)

1. **Modificar `ai_product_extractor.py`:**
   - Substituir chamada OpenAI por chamada HTTP ao OpenMind AI
   - Manter mesma interface (mesmo retorno)
   - Adicionar configuração via variáveis de ambiente

2. **Atualizar `settings.py`:**
   - Adicionar configurações do OpenMind AI
   - Manter compatibilidade com OpenAI (fallback opcional)

3. **Atualizar `environment_variables.example`:**
   - Adicionar variáveis do OpenMind AI (já feito)

### Fase 2: Implementar Servidor OpenMind AI

1. Criar endpoint `/api/v1/analyze-product-image` no SinapUm
2. Implementar análise de imagens (similar ao GPT-4o Vision)
3. Retornar JSON no formato ÉVORA
4. Configurar autenticação por API key

### Fase 3: Testes e Ajustes

1. Testar integração end-to-end
2. Comparar resultados OpenMind AI vs OpenAI
3. Ajustar prompts/formatação conforme necessário

---

## 📝 Mudanças Necessárias

### Arquivo: `app_marketplace/ai_product_extractor.py`

**Antes (OpenAI):**
```python
client = OpenAI(api_key=api_key)
response = client.chat.completions.create(...)
```

**Depois (OpenMind AI):**
```python
import requests
response = requests.post(
    OPENMIND_AI_URL + '/analyze-product-image',
    files={'image': image_file},
    headers={'Authorization': f'Bearer {OPENMIND_AI_KEY}'}
)
```

### Configuração

**Variáveis de Ambiente:**
```bash
AI_SERVICE=openmind  # Usar OpenMind AI
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=sua-api-key
OPENMIND_AI_TIMEOUT=30
```

---

## ✅ Próximos Passos

1. ✅ Documentar o que existe (este documento)
2. ⏳ **Adaptar `ai_product_extractor.py` para OpenMind AI** ← FOCO AGORA
3. ⏳ Implementar servidor OpenMind AI no SinapUm
4. ⏳ Testar integração
5. ⏳ Remover dependência da OpenAI (opcional)

---

## 🔗 Referências

- [`_doc/ESPECIFICACAO_API_OPENMIND_AI.md`](ESPECIFICACAO_API_OPENMIND_AI.md) - Especificação da API
- [`_doc/INTEGRACAO_OPENMIND_AI.md`](INTEGRACAO_OPENMIND_AI.md) - Visão geral da integração
- [`_doc/SINAPUM_SERVER_INFO.md`](SINAPUM_SERVER_INFO.md) - Informações do servidor
