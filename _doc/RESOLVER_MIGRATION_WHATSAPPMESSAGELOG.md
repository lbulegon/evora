# 🔧 Resolver Migration: WhatsappMessageLog

## ❌ Erro Atual

```
It is impossible to add a non-nullable field 'content' to whatsappmessagelog without specifying a default.
Please select a fix:
 1) Provide a one-off default now (will be set on all existing rows with a null value for this column)
 2) Quit and manually define a default value in models.py.
Select an option: 1
Please enter the default value as valid Python.
```

## ✅ Solução

### Opção 1: Fornecer valor padrão no prompt

No terminal, quando pedir o valor padrão, digite:

```
''
```

Isso define uma **string vazia** como padrão para o campo `content`.

### Opção 2: Cancelar e corrigir no modelo

Se preferir, pode cancelar (digite `exit`) e depois:

1. Encontrar o modelo `WhatsappMessageLog`
2. Tornar o campo `content` nullable ou adicionar `default=''`

## 📝 Como proceder

**No terminal interativo, digite:**

```
''
```

**Depois pressione Enter**

O Django irá:
- Aplicar a string vazia como padrão para todas as linhas existentes
- Continuar criando a migration

---

**Nota:** Se o modelo `WhatsappMessageLog` não existe mais ou foi renomeado, pode ser necessário verificar as migrations anteriores.

