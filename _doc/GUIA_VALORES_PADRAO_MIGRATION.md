# 📝 Guia: Valores Padrão para Migration WhatsappMessageLog

## Campos Solicitados

A migration está pedindo valores padrão para campos obrigatórios no modelo `WhatsappMessageLog`:

### 1. Campo `content` (já respondido)
```
Valor: ''
```

### 2. Campo `timestamp` (atual)
```
Valor: timezone.now
```

## ✅ Como Proceder

No terminal, quando perguntar o valor padrão para `timestamp`, digite:

```
timezone.now
```

Depois pressione **Enter**.

## 📋 Ordem Esperada

Se pedir mais campos, os valores padrão típicos são:

- **content** (Text): `''` (string vazia)
- **timestamp** (DateTime): `timezone.now`
- **created_at** (DateTime): `timezone.now`
- **updated_at** (DateTime): `timezone.now`

## ⚠️ Importante

- `timezone.now` **NÃO** precisa de aspas (não é string, é função)
- O Django já tem o módulo `timezone` disponível no contexto

---

**Continue digitando os valores conforme solicitado pelo Django!**

