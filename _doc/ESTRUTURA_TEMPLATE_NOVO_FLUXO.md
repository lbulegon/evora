# 📱 Estrutura do Novo Template - Fluxo em 4 Etapas

## 🎯 Etapas do Fluxo

### Etapa 1: Captura de Fotos
**ID:** `stepCard1`

**Funcionalidades:**
- Câmera ou galeria
- Capturar múltiplas fotos
- Preview de todas as fotos em grid
- Botão "Remover" em cada foto
- Botão "Adicionar Mais Fotos"
- Botão "Verificar Produto" (vai para Etapa 2)

**Estado:**
- Array `capturedPhotos = []` armazena todas as fotos
- Cada foto tem: `{ blob, preview, id }`

### Etapa 2: Verificação
**ID:** `stepCard2`

**Funcionalidades:**
- Envia todas as fotos para `/api/produtos/verificar_produto/`
- Mostra loading durante verificação
- Resultado:
  - ✅ "Todas as fotos são do mesmo produto" → Botão "Análise Completa"
  - ⚠️ "Produtos diferentes detectados" → Botão "Voltar" para remover fotos

**Estado:**
- `verificationResult = null`

### Etapa 3: Análise Completa
**ID:** `stepCard3`

**Funcionalidades:**
- Envia todas as fotos para `/api/produtos/analise_completa/`
- Mostra progresso (loading)
- Gera JSON completo
- Botão "Revisar e Salvar" (vai para Etapa 4)

**Estado:**
- `produtoJson = null`
- `imageUrls = []`
- `imagePaths = []`

### Etapa 4: Revisão e Salvamento
**ID:** `stepCard4`

**Funcionalidades:**
- Mostra JSON gerado (editável)
- Preview de todas as imagens
- Campos editáveis (nome, marca, categoria, etc.)
- Botão "Salvar no Banco" → `/api/produtos/salvar_json/`
- Sucesso → Mensagem de confirmação

**Estado:**
- `produtoJson` editado
- Campos do formulário preenchidos

---

## 🔧 JavaScript Necessário

### Variáveis Globais
```javascript
let capturedPhotos = [];  // Array de fotos capturadas
let currentStep = 1;
let verificationResult = null;
let produtoJson = null;
let imageUrls = [];
let imagePaths = [];
```

### Funções Principais

1. **Captura:**
   - `capturePhoto()` - Captura foto da câmera
   - `addPhotoFromGallery()` - Adiciona da galeria
   - `removePhoto(index)` - Remove foto do array
   - `renderPhotoGrid()` - Renderiza grid de previews

2. **Verificação:**
   - `verifyProduct()` - Envia para verificação
   - `handleVerificationResult()` - Processa resultado

3. **Análise:**
   - `analyzeComplete()` - Envia para análise completa
   - `handleAnalysisResult()` - Processa JSON gerado

4. **Salvamento:**
   - `saveProduct()` - Salva no banco
   - `handleSaveResult()` - Processa resultado

5. **Navegação:**
   - `goToStep(step)` - Navega entre etapas
   - `updateStepIndicator()` - Atualiza indicador visual

---

## 📋 Estrutura HTML

```html
<!-- Indicador de Passos (4 etapas) -->
<div class="step-indicator">
    <div class="step-dot active" id="step1">1</div>
    <div class="step-line" id="line1"></div>
    <div class="step-dot" id="step2">2</div>
    <div class="step-line" id="line2"></div>
    <div class="step-dot" id="step3">3</div>
    <div class="step-line" id="line3"></div>
    <div class="step-dot" id="step4">4</div>
</div>

<!-- Etapa 1: Captura -->
<div class="step-card active" id="stepCard1">
    <!-- Câmera/Galeria -->
    <!-- Grid de fotos capturadas -->
    <!-- Botões: Adicionar, Remover, Verificar -->
</div>

<!-- Etapa 2: Verificação -->
<div class="step-card" id="stepCard2">
    <!-- Loading -->
    <!-- Resultado da verificação -->
    <!-- Botões: Voltar, Análise Completa -->
</div>

<!-- Etapa 3: Análise Completa -->
<div class="step-card" id="stepCard3">
    <!-- Loading -->
    <!-- Progresso -->
    <!-- Botão: Revisar e Salvar -->
</div>

<!-- Etapa 4: Revisão e Salvamento -->
<div class="step-card" id="stepCard4">
    <!-- Formulário editável -->
    <!-- Preview de imagens -->
    <!-- Editor JSON -->
    <!-- Botão: Salvar no Banco -->
</div>
```

---

**Status:** 📝 **ESTRUTURA DEFINIDA - AGUARDANDO IMPLEMENTAÇÃO**

