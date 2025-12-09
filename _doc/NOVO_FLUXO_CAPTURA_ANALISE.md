# 🔄 Novo Fluxo de Captura, Análise e Salvamento

## 📋 Resumo das Mudanças

O fluxo foi reestruturado em **4 etapas claras**:

1. **Etapa 1: Captura de Fotos** - Capturar múltiplas fotos, escolher quais manter/remover
2. **Etapa 2: Verificação** - Primeira análise para verificar se são do mesmo produto
3. **Etapa 3: Análise Completa** - Segunda análise completa para gerar JSON
4. **Etapa 4: Revisão e Salvamento** - Revisar JSON e salvar no banco

---

## 🚀 Novos Endpoints Criados

### 1. `POST /api/produtos/verificar_produto/`
**Função:** `verificar_produto_fotos()`

**Propósito:** Primeira análise - verificar se múltiplas fotos são do mesmo produto

**Entrada:**
- `images[]` - Array de arquivos de imagem

**Saída:**
```json
{
  "success": true,
  "mesmo_produto": true/false,
  "consistencia": {
    "mesmo_produto": true,
    "confianca": 0.95,
    "detalhes": {...}
  },
  "total_imagens": 3,
  "aviso": "..." (se produtos diferentes)
}
```

### 2. `POST /api/produtos/analise_completa/`
**Função:** `analise_completa_produto()`

**Propósito:** Segunda análise completa - gerar JSON completo do produto

**Entrada:**
- `images[]` - Array de arquivos de imagem (do mesmo produto)

**Saída:**
```json
{
  "success": true,
  "produto_json": {
    "produto": {...},
    "produto_generico_catalogo": {...},
    ...
  },
  "image_urls": [...],
  "image_paths": [...],
  "saved_filenames": [...],
  "total_imagens": 3
}
```

---

## 📱 Fluxo de Interface

### Etapa 1: Captura de Fotos
- ✅ Câmera ou galeria
- ✅ Capturar múltiplas fotos
- ✅ Preview de todas as fotos capturadas
- ✅ Botão para remover cada foto
- ✅ Botão para adicionar mais fotos
- ✅ Botão "Verificar Produto" para próxima etapa

### Etapa 2: Verificação
- ✅ Envia todas as fotos para verificação
- ✅ Mostra resultado: "São do mesmo produto" ou "Produtos diferentes"
- ✅ Se diferentes: permite voltar e remover fotos
- ✅ Se iguais: botão "Análise Completa" para próxima etapa

### Etapa 3: Análise Completa
- ✅ Envia todas as fotos para análise completa
- ✅ Mostra progresso (loading)
- ✅ Gera JSON completo
- ✅ Botão "Revisar e Salvar" para próxima etapa

### Etapa 4: Revisão e Salvamento
- ✅ Mostra JSON gerado
- ✅ Permite edição (se necessário)
- ✅ Mostra preview das imagens
- ✅ Botão "Salvar no Banco" para finalizar

---

## 🔧 Modificações no Código

### Views (`product_photo_views.py`)

**Novas funções:**
1. `verificar_produto_fotos()` - Verificação inicial
2. `analise_completa_produto()` - Análise completa

**Mantidas:**
- `detect_product_by_photo()` - Para compatibilidade
- `save_product_json()` - Para salvamento final

### URLs (`urls.py`)

**Adicionadas:**
```python
path('api/produtos/verificar_produto/', product_photo_views.verificar_produto_fotos, name='api_verificar_produto'),
path('api/produtos/analise_completa/', product_photo_views.analise_completa_produto, name='api_analise_completa'),
```

---

## 📝 Próximos Passos

1. ✅ Endpoints criados
2. ⏳ Template atualizado (em progresso)
3. ⏳ JavaScript para gerenciar fluxo (em progresso)
4. ⏳ Testes

---

**Status:** 🚧 **EM DESENVOLVIMENTO**

