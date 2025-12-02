# Integração OpenMind AI - Servidor de Inteligência Artificial Próprio

Este documento descreve a integração do ÉVORA Connect com o servidor OpenMind AI, substituindo ou complementando a OpenAI Vision API.

---

## Visão Geral

O sistema ÉVORA atualmente usa **OpenAI Vision API (GPT-4o)** para análise de imagens de produtos. O objetivo é migrar para um **servidor próprio OpenMind AI** hospedado no servidor **SinapUm**.

---

## Arquitetura Proposta

### Fluxo Atual (OpenAI)
```
ÉVORA → OpenAI Vision API (GPT-4o) → JSON ÉVORA
```

### Fluxo Novo (OpenMind AI)
```
ÉVORA → Servidor OpenMind AI (SinapUm) → JSON ÉVORA
```

---

## Configuração do Servidor OpenMind AI

### Requisitos do Servidor

1. **API REST** para receber imagens
2. **Análise de imagens** similar ao GPT-4o Vision
3. **Resposta em JSON** no padrão ÉVORA
4. **Autenticação** (API key ou token)

### Endpoint Esperado

```http
POST https://openmind-ai.sinapum.com/api/v1/analyze-product-image
Content-Type: multipart/form-data
Authorization: Bearer {API_KEY}

{
  "image": <arquivo_imagem>
}
```

**Nota:** A URL acima é um exemplo. A URL real do servidor SinapUm será definida na configuração.

### Resposta Esperada

```json
{
  "success": true,
  "data": {
    "nome_produto": "...",
    "categoria": "...",
    "subcategoria": "...",
    "descricao": "...",
    "caracteristicas": {...},
    "compatibilidade": {...},
    "codigo_barras": "...",
    ...
  }
}
```

---

## Implementação no ÉVORA

### 1. Módulo de IA Flexível

Criar `app_marketplace/ai_service.py` que suporte:
- OpenAI (atual)
- OpenMind AI (novo)
- Configuração via variáveis de ambiente

### 2. Variáveis de Ambiente

```bash
# Escolher serviço de IA
AI_SERVICE=openmind  # ou "openai"

# OpenAI (se AI_SERVICE=openai)
OPENAI_API_KEY=sk-...

# OpenMind AI (se AI_SERVICE=openmind)
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1  # URL do servidor SinapUm (IP: 69.169.102.84)
# ou se tiver domínio:
# OPENMIND_AI_URL=https://openmind.sinapum.com/api/v1
OPENMIND_AI_KEY=your-api-key-here
OPENMIND_AI_TIMEOUT=30
```

### 3. Adaptação do Código

O código atual em `ai_product_extractor.py` será adaptado para:
- Verificar qual serviço está configurado
- Chamar o serviço apropriado
- Tratar respostas de ambos os formatos

---

## Checklist de Implementação

### Backend (Django)

- [ ] Criar módulo `ai_service.py` com suporte a múltiplos provedores
- [ ] Adaptar `ai_product_extractor.py` para usar o módulo flexível
- [ ] Adicionar configurações em `settings.py`
- [ ] Criar testes para ambos os serviços
- [ ] Documentar diferenças entre os serviços

### Frontend

- [ ] (Nenhuma mudança necessária - API permanece a mesma)

### Servidor OpenMind AI

- [ ] Implementar endpoint `/api/v1/analyze-product-image`
- [ ] Suportar upload de imagem (multipart/form-data)
- [ ] Retornar JSON no formato ÉVORA
- [ ] Implementar autenticação
- [ ] Adicionar rate limiting
- [ ] Documentar API

---

## Testes

### Teste Local (OpenMind AI)

```python
from app_marketplace.ai_service import analyze_product_image

result = analyze_product_image(image_file)
assert result['success'] == True
assert 'nome_produto' in result['data']
```

### Teste de Comparação

Testar com a mesma imagem em ambos os serviços e comparar resultados.

---

## Migração

### Fase 1: Preparação
- Implementar módulo flexível
- Configurar variáveis de ambiente
- Testar em ambiente de desenvolvimento

### Fase 2: Teste Paralelo
- Rodar ambos os serviços simultaneamente
- Comparar resultados
- Ajustar prompts/formatação do OpenMind AI

### Fase 3: Migração Gradual
- Migrar parte do tráfego para OpenMind AI
- Monitorar qualidade dos resultados
- Ajustar conforme necessário

### Fase 4: Migração Completa
- Desativar OpenAI (ou manter como fallback)
- Usar OpenMind AI como principal
- Monitorar performance e custos

---

## Próximos Passos

1. **Definir especificações da API OpenMind AI**
2. **Implementar módulo flexível no ÉVORA**
3. **Testar integração**
4. **Documentar API do servidor OpenMind AI**
5. **Criar plano de migração**

---

## Referências

- [OpenAI Vision API](https://platform.openai.com/docs/guides/vision)
- [Django REST Framework](https://www.django-rest-framework.org/)
- Servidor: **SinapUm** (SSH conectado)
