# ✅ Checklist - Integrar OpenMind.org API

## 📋 Informações Necessárias

- [ ] **URL base da API do OpenMind.org**
  - Exemplo: `https://api.openmind.org/v1/`
  - Onde encontrar: https://portal.openmind.org/

- [ ] **Método de autenticação**
  - Como usar a chave `om1_live_...`?
  - Formato do header?
  - `Authorization: Bearer om1_live_...`?
  - Ou outro formato?

- [ ] **Endpoint para análise de imagens**
  - Qual endpoint usar?
  - Suporta análise de imagens?
  - Exemplo: `/v1/chat/completions` ou `/v1/vision/analyze`?

- [ ] **Formato da requisição**
  - Como enviar imagem?
  - Base64?
  - URL?
  - Multipart/form-data?

- [ ] **Formato da resposta**
  - JSON?
  - Estrutura específica?
  - Exemplo de resposta?

---

## 🔧 Adaptações Necessárias no Código

### 1. Modificar `image_analyzer.py`

- [ ] Substituir chamada OpenAI por OpenMind.org
- [ ] Adaptar formato de autenticação
- [ ] Adaptar formato de requisição
- [ ] Adaptar parsing da resposta

### 2. Atualizar `config.py`

- [ ] Adicionar configurações do OpenMind.org
- [ ] URL da API
- [ ] Chave de autenticação
- [ ] Modelo a usar (se aplicável)

### 3. Atualizar `.env.example`

- [ ] Documentar variáveis do OpenMind.org
- [ ] Remover ou marcar OpenAI como opcional

---

## 🧪 Testes

- [ ] Testar autenticação
- [ ] Testar envio de imagem
- [ ] Testar parsing da resposta
- [ ] Testar end-to-end no ÉVORA

---

## 📝 Documentação

- [ ] Atualizar documentação da integração
- [ ] Explicar como configurar OpenMind.org
- [ ] Remover referências a OpenAI como obrigatório

---

**Vamos começar descobrindo a API do OpenMind.org!** 🚀
