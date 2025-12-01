# Onde os Dados das Configurações são Salvos

Este documento explica onde cada dado da página de configurações (`/settings/`) é salvo no banco de dados PostgreSQL.

## 📋 Estrutura de Armazenamento

### 1. **Dados Básicos do Usuário**

**Tabela:** `auth_user` (Django padrão)

**Campos salvos:**
- `first_name` → Nome
- `last_name` → Sobrenome  
- `email` → E-mail
- `password` → Senha (hash criptografado)

**Código:** `user_settings_views.py` - função `update_profile()` linhas 62-69

```python
user.first_name = request.POST['first_name']
user.last_name = request.POST['last_name']
user.email = request.POST['email']
user.save()  # Salva na tabela auth_user
```

---

### 2. **Dados do Perfil - Personal Shopper**

**Tabela:** `app_marketplace_personalshopper`

**Campos salvos:**
- `telefone` → Telefone
- `bio` → Biografia

**Relação:**
- `user_id` (FK) → referencia `auth_user.id` (OneToOneField)

**Código:** `user_settings_views.py` - função `update_profile()` linhas 72-79

```python
if user.is_shopper:
    profile = getattr(user, 'personalshopper', None)
    if profile:
        if 'phone' in request.POST:
            profile.telefone = request.POST['phone']
        if 'bio' in request.POST:
            profile.bio = request.POST['bio']
        profile.save()  # Salva na tabela app_marketplace_personalshopper
```

---

### 3. **Dados do Perfil - Address Keeper**

**Tabela:** `app_marketplace_addresskeeper`

**Campos salvos:**
- `telefone` → Telefone
- `endereco` → Endereço

**Relação:**
- `user_id` (FK) → referencia `auth_user.id` (OneToOneField)

**Código:** `user_settings_views.py` - função `update_profile()` linhas 81-88

```python
elif user.is_address_keeper:
    profile = getattr(user, 'address_keeper', None)
    if profile:
        if 'phone' in request.POST:
            profile.telefone = request.POST['phone']
        if 'address' in request.POST:
            profile.endereco = request.POST['address']
        profile.save()  # Salva na tabela app_marketplace_addresskeeper
```

---

### 4. **Dados do Perfil - Cliente**

**Tabela:** `app_marketplace_cliente`

**Campos salvos:**
- `telefone` → Telefone

**Relação:**
- `user_id` (FK) → referencia `auth_user.id` (OneToOneField)

**Código:** `user_settings_views.py` - função `update_profile()` linhas 90-95

```python
elif user.is_cliente:
    profile = getattr(user, 'cliente', None)
    if profile:
        if 'phone' in request.POST:
            profile.telefone = request.POST['phone']
        profile.save()  # Salva na tabela app_marketplace_cliente
```

---

### 5. **Senha**

**Tabela:** `auth_user` (campo `password`)

**Processo:**
- A senha é criptografada usando o sistema de hash do Django
- Usa `PasswordChangeForm` do Django para validação
- Mantém o usuário logado após a alteração

**Código:** `user_settings_views.py` - função `change_password()` linhas 107-120

```python
form = PasswordChangeForm(request.user, request.POST)
if form.is_valid():
    user = form.save()  # Salva senha hash na tabela auth_user
    update_session_auth_hash(request, user)  # Mantém sessão ativa
```

---

## 🔗 Relacionamento entre Tabelas

```
auth_user (Django User)
├── id (PK)
├── username
├── first_name
├── last_name
├── email
├── password (hash)
└── ...
    │
    ├──→ app_marketplace_personalshopper (OneToOne)
    │   ├── user_id (FK)
    │   ├── telefone
    │   └── bio
    │
    ├──→ app_marketplace_addresskeeper (OneToOne)
    │   ├── user_id (FK)
    │   ├── telefone
    │   └── endereco
    │
    └──→ app_marketplace_cliente (OneToOne)
        ├── user_id (FK)
        └── telefone
```

---

## 📝 Endpoints de Salvamento

| Ação | Endpoint | Método | Tabela(s) Afetada(s) |
|------|----------|--------|---------------------|
| Atualizar Perfil | `/settings/profile/update/` | POST | `auth_user` + tabela do perfil específico |
| Alterar Senha | `/settings/password/change/` | POST | `auth_user` (campo `password`) |

---

## 🔍 Consultas SQL de Exemplo

### Ver dados do usuário:
```sql
SELECT id, username, first_name, last_name, email 
FROM auth_user 
WHERE username = 'seu_usuario';
```

### Ver perfil Personal Shopper:
```sql
SELECT ps.*, u.username, u.email 
FROM app_marketplace_personalshopper ps
JOIN auth_user u ON ps.user_id = u.id
WHERE u.username = 'seu_usuario';
```

### Ver perfil Cliente:
```sql
SELECT c.*, u.username, u.email 
FROM app_marketplace_cliente c
JOIN auth_user u ON c.user_id = u.id
WHERE u.username = 'seu_usuario';
```

---

## ⚠️ Nota sobre Conexão WhatsApp

**A conexão WhatsApp não é salva no banco de dados Django.**

A conexão é gerenciada pelo serviço **WPPConnect** (rodando separadamente), que mantém:
- Sessões em memória ou arquivo
- QR Codes temporários
- Status de conexão

O ÉVORA apenas **consulta** o status da conexão via API do WPPConnect, mas não armazena os dados de sessão do WhatsApp no PostgreSQL.

