# Fluxo de Cadastro de Produto por Foto - VitrineZap

## 📸 Inspirado no App de Nutrição

Este fluxo foi inspirado no aplicativo de nutrição que tira foto de refeições, adaptado para produtos de venda no VitrineZap.

---

## 🔄 Fluxo Completo

### 1. **Início do Cadastro**
- Usuário (Shopper) acessa "Meus Produtos"
- Clica no botão **"Cadastrar por Foto"**
- Abre a página de captura de foto

### 2. **Captura da Foto**
- Usuário pode:
  - **Tirar foto com a câmera** do dispositivo
  - **Escolher da galeria** de fotos
- Foto é capturada do rótulo/etiqueta do produto

### 3. **Análise com IA**
- Foto é enviada para o backend
- **IA (OpenAI Vision) analisa a imagem:**
  - Extrai nome do produto do rótulo
  - Identifica marca
  - Detecta peso/volume (ex: "250g", "1L", "M", "P")
  - Lê código de barras (se visível)
  - Sugere categoria (ex: "Lingerie", "Cosmético", "Bebida")
  - Captura preço (se estiver na etiqueta)
  - Extrai outras informações visíveis

### 4. **Formulário Pré-preenchido**
- Tela de cadastro retorna **pré-preenchida** com dados extraídos
- Usuário pode:
  - ✅ Conferir informações
  - ✅ Ajustar campos errados
  - ✅ Completar dados faltantes
  - ✅ Ajustar preço de venda
  - ✅ Selecionar grupo WhatsApp

### 5. **Salvamento**
- Ao salvar, o produto:
  - É salvo na base de produtos do VitrineZap
  - **Imagem é salva de forma recuperável** em `media/produtos/{user_id}/`
  - Fica disponível para campanhas e mensagens de WhatsApp
  - Pode ser visualizado posteriormente com a imagem original

---

## 🎯 Características Especiais

### **Apenas para Produtos de Venda**
- Botão "Cadastrar por Foto" aparece apenas para produtos de venda
- Produtos internos (embalagens, materiais) usam upload normal

### **Imagem Recuperável**
- Imagem salva em localização permanente
- URL armazenada em `WhatsappProduct.image_urls`
- Pode ser consultada e exibida ao visualizar o produto

### **Editor JSON (Futuro)**
- Dados extraídos podem ser editados em formato JSON antes de salvar
- Permite ajustar informações erradas da IA

---

## 📋 Estrutura de Dados

### **Resposta da IA:**
```json
{
    "nome_sugerido": "Conjunto de lingerie renda preta",
    "marca_sugerida": "Júnior Lingeries",
    "peso_volume": "M",
    "codigo_barras": "7891234567890",
    "categoria_sugerida": "Lingerie",
    "preco_visivel": "15.90",
    "descricao_observacoes": "Conjunto com sutiã e calcinha",
    "caracteristicas": ["renda", "preto"],
    "pais_origem": "Brasil",
    "condicao": "novo"
}
```

### **Produto Salvo:**
```json
{
    "id": "prod_123",
    "name": "Conjunto de lingerie renda preta",
    "brand": "Júnior Lingeries",
    "price": 15.90,
    "image_urls": ["https://.../produtos/user_id/timestamp_produto.jpg"],
    "category": "Lingerie",
    "codigo_barras": "7891234567890"
}
```

---

## 🔗 Integração com KMN

- Produto de venda nasce a partir da foto
- Pode ser compartilhado na rede KMN
- Foto original serve para todos os participantes
- Cada Keeper pode adicionar fotos adicionais

---

## 🛠️ Endpoints da API

### **1. Analisar Foto**
```
POST /api/produtos/detectar_por_foto/
Content-Type: multipart/form-data

image: arquivo da foto
```

**Resposta:**
```json
{
    "success": true,
    "product_data": {
        "nome_sugerido": "...",
        "marca_sugerida": "...",
        ...
    },
    "image_url": "https://.../produtos/temp/user_id/timestamp_temp.jpg"
}
```

### **2. Salvar Produto**
```
POST /api/produtos/salvar_por_foto/
Content-Type: application/json

{
    "name": "Nome do produto",
    "group_id": 1,
    "image_url": "https://.../temp/...",
    "price": "15.90",
    "brand": "Marca",
    "category": "Categoria",
    ...
}
```

**Resposta:**
```json
{
    "success": true,
    "product": {
        "id": 123,
        "name": "...",
        "image_url": "https://.../produtos/user_id/timestamp_produto.jpg"
    }
}
```

---

## 📱 Interface do Usuário

1. **Botão "Cadastrar por Foto"**
   - Visível apenas para produtos de venda
   - Abre página de captura

2. **Tela de Captura**
   - Botão câmera
   - Botão galeria
   - Preview da foto

3. **Análise em Progresso**
   - Loading enquanto IA processa
   - Mensagem: "Analisando imagem..."

4. **Formulário Pré-preenchido**
   - Campos editáveis
   - Validação
   - Seleção de grupo WhatsApp

5. **Confirmação**
   - Produto salvo com sucesso
   - Redirecionamento opcional

---

## ✅ Benefícios

- ✅ **Rapidez**: Cadastro muito mais rápido
- ✅ **Precisão**: IA extrai dados do rótulo automaticamente
- ✅ **Facilidade**: Menos digitação, mais praticidade
- ✅ **Recuperabilidade**: Imagem salva permanentemente
- ✅ **Edição**: Dados podem ser ajustados antes de salvar

