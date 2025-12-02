# 🔑 Diagrama - Onde Cada Chave Fica e Para Que Serve

## 📍 Localização das Chaves

### ÉVORA (Railway)

```
Variáveis no Railway:
├── AI_SERVICE=openmind  (escolhe qual serviço usar)
├── OPENMIND_AI_URL=...  (onde está o servidor)
├── OPENMIND_AI_KEY=om1_live_...  (autentica COM servidor)
└── OPENAI_API_KEY=sk-...  (opcional, para fallback direto)
```

**Uso:** Envia requisições para o servidor OpenMind AI

---

### Servidor OpenMind AI (SinapUm)

```
Variáveis no servidor:
├── OPENMIND_AI_API_KEY=om1_live_...  (recebe requisições do ÉVORA)
└── OPENAI_API_KEY=sk-...  (← FALTA! Usa para analisar imagens)
```

**Uso:** Recebe requisições e analisa imagens internamente

---

## 🔄 Fluxo Simplificado

```
ÉVORA                          OpenMind AI (SinapUm)
  │                                 │
  │ ──OPENMIND_AI_KEY──────────> │  (autentica)
  │   (Envia imagem)               │
  │                                 │ ──OPENAI_API_KEY──> OpenAI
  │                                 │   (analisa imagem)
  │                                 │ <─── Dados ──────── OpenAI
  │ <────── JSON ──────────────│  (retorna dados)
  │                                 │
```

---

## ✅ Status Atual

| Chave | Onde | Para Que Serve | Status |
|-------|------|----------------|--------|
| `OPENMIND_AI_KEY` | Railway | Autenticar com servidor | ✅ OK |
| `OPENMIND_AI_API_KEY` | SinapUm | Receber requisições | ✅ OK |
| `OPENAI_API_KEY` | SinapUm | Analisar imagens | ❌ **FALTA** |

---

**A única coisa que falta é configurar `OPENAI_API_KEY` no SinapUm!** 🎯
