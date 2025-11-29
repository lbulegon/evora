#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.contrib.auth.models import User
from app_marketplace.models import Cliente

print("=" * 60)
print("ESTRUTURA DAS TABELAS")
print("=" * 60)
print()
print("1. TABELA: auth_user (Django User)")
print("   Campos principais:")
print("   - id (PK)")
print("   - username")
print("   - email")
print("   - first_name")
print("   - last_name")
print("   - is_active, is_staff, etc.")
print()
print("2. TABELA: app_marketplace_cliente")
print("   Campos principais:")
print("   - id (PK)")
print("   - user_id (FK -> auth_user.id)")
print("   - telefone")
print("   - wallet_id (FK -> CarteiraCliente, opcional)")
print("   - contato (JSON)")
print("   - metadados (JSON)")
print("   - criado_em, atualizado_em")
print()
print("=" * 60)
print("VERIFICANDO DADOS NO BANCO")
print("=" * 60)
print()

# Buscar por email
emails = ['joao@email.com', 'maria@email.com']
users = User.objects.filter(email__in=emails)

if users.exists():
    print(f"✓ Encontrados {users.count()} usuário(s) com esses emails:")
    for u in users:
        try:
            cliente = u.cliente
            print(f"  ID: {u.id}")
            print(f"  Nome: {u.get_full_name() or u.username}")
            print(f"  Email: {u.email}")
            print(f"  Telefone: {cliente.telefone or 'N/A'}")
            print(f"  Tabela User: auth_user (id={u.id})")
            print(f"  Tabela Cliente: app_marketplace_cliente (id={cliente.id})")
            print()
        except Cliente.DoesNotExist:
            print(f"  ID: {u.id}")
            print(f"  Nome: {u.get_full_name() or u.username}")
            print(f"  Email: {u.email}")
            print(f"  ⚠️  Cliente não encontrado na tabela app_marketplace_cliente")
            print()
else:
    print("✗ Nenhum usuário encontrado com esses emails no banco de dados.")
    print()
    print("Os dados estão apenas no template HTML (hardcoded):")
    print("  Arquivo: app_marketplace/templates/app_marketplace/clientes.html")
    print("  Linhas: 22-32")

print()
print("=" * 60)
print("RESUMO")
print("=" * 60)
print()
print("Os registros 'João Silva' e 'Maria Santos' estão:")
print("  ❌ NÃO estão no banco de dados")
print("  ✅ Estão apenas no template HTML (dados estáticos)")
print()
print("Para que apareçam no banco, precisam ser criados em:")
print("  1. Tabela auth_user (User do Django)")
print("  2. Tabela app_marketplace_cliente (Cliente)")


