# ⏰ Timestamp Válido para Migration

## ✅ Opção Recomendada

Para o campo `timestamp`, digite no terminal:

```
timezone.now
```

**Sem aspas!** Isso usará a data/hora atual como padrão.

## 🔄 Outras Opções Válidas

Se precisar de uma data específica, você pode usar:

### Data/Hora Específica
```
timezone.datetime(2025, 1, 1, 0, 0, 0)
```

### Data Atual (alternativa)
```
timezone.now()
```

## 📝 Explicação

- `timezone.now` é uma **referência à função** - será executada para cada registro
- `timezone.now()` seria executado uma única vez na criação da migration
- O Django já importa `timezone` automaticamente no contexto da migration

---

**Para seu caso, digite:**
```
timezone.now
```

E pressione Enter.

