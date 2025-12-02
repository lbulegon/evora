# 🎯 Integração OpenMind.org - Completa

Baseado na documentação: https://docs.openmind.org/api-reference/introduction

---

## ✅ Informações Confirmadas

### 1. URL da API

**Base URL:** `https://api.openmind.org`

**Endpoint para Chat Completions:**
```
POST https://api.openmind.org/api/core/openai/chat/completions
```

### 2. Autenticação

**Formato:**
```http
Authorization: Bearer om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
```

**Ou:**
```http
x-api-key: om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
```

### 3. Modelos de Visão Disponíveis

- **qwen2.5-vl-72b-instruct** - $0.59/$0.59 por 1M tokens
- **GPT-4o** - $2.5/$10 por 1M tokens (mais caro)

---

## 🔧 Adaptação do Código

A API do OpenMind.org parece ser **compatível com OpenAI API**, então a adaptação será simples!

Vou modificar o código para usar OpenMind.org ao invés de OpenAI diretamente.

---

## 📋 Próximos Passos

1. Adaptar `image_analyzer.py` para usar OpenMind.org
2. Configurar URL e autenticação
3. Testar integração

**Vou fazer isso agora!** 🚀
