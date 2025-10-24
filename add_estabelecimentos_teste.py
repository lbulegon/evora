#!/usr/bin/env python
"""
Script para adicionar estabelecimentos de teste
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from app_marketplace.models import Estabelecimento

def create_test_establishments():
    """Criar estabelecimentos de teste"""
    print("🏪 Criando estabelecimentos de teste...")
    
    establishments = [
        {
            'nome': 'Victoria\'s Secret - Orlando Premium Outlets',
            'endereco': '8200 Vineland Ave, Orlando, FL 32821',
            'cidade': 'Orlando',
            'estado': 'FL',
            'pais': 'USA',
            'telefone': '+1 (407) 238-7787',
            'website': 'https://www.victoriassecret.com',
            'horario_funcionamento': 'Seg-Dom: 9h-21h',
            'categorias': ['Perfumes', 'Lingerie', 'Cosméticos'],
            'ativo': True
        },
        {
            'nome': 'Nike Store - Orlando Premium Outlets',
            'endereco': '8200 Vineland Ave, Orlando, FL 32821',
            'cidade': 'Orlando',
            'estado': 'FL',
            'pais': 'USA',
            'telefone': '+1 (407) 238-7787',
            'website': 'https://www.nike.com',
            'horario_funcionamento': 'Seg-Dom: 9h-21h',
            'categorias': ['Calçados', 'Roupas Esportivas', 'Acessórios'],
            'ativo': True
        },
        {
            'nome': 'Target - International Drive',
            'endereco': '8250 International Dr, Orlando, FL 32819',
            'cidade': 'Orlando',
            'estado': 'FL',
            'pais': 'USA',
            'telefone': '+1 (407) 352-0000',
            'website': 'https://www.target.com',
            'horario_funcionamento': 'Seg-Dom: 7h-23h',
            'categorias': ['Eletrônicos', 'Roupas', 'Casa', 'Cosméticos'],
            'ativo': True
        },
        {
            'nome': 'Walmart Supercenter - Kissimmee',
            'endereco': '3250 Vineland Rd, Kissimmee, FL 34746',
            'cidade': 'Kissimmee',
            'estado': 'FL',
            'pais': 'USA',
            'telefone': '+1 (407) 397-0000',
            'website': 'https://www.walmart.com',
            'horario_funcionamento': '24 horas',
            'categorias': ['Alimentação', 'Eletrônicos', 'Roupas', 'Casa', 'Farmacia'],
            'ativo': True
        },
        {
            'nome': 'Macy\'s - Florida Mall',
            'endereco': '8001 S Orange Blossom Trl, Orlando, FL 32809',
            'cidade': 'Orlando',
            'estado': 'FL',
            'pais': 'USA',
            'telefone': '+1 (407) 851-6200',
            'website': 'https://www.macys.com',
            'horario_funcionamento': 'Seg-Sab: 10h-21h, Dom: 11h-19h',
            'categorias': ['Roupas', 'Calçados', 'Acessórios', 'Cosméticos', 'Casa'],
            'ativo': True
        },
        {
            'nome': 'Sephora - Florida Mall',
            'endereco': '8001 S Orange Blossom Trl, Orlando, FL 32809',
            'cidade': 'Orlando',
            'estado': 'FL',
            'pais': 'USA',
            'telefone': '+1 (407) 851-6200',
            'website': 'https://www.sephora.com',
            'horario_funcionamento': 'Seg-Sab: 10h-21h, Dom: 11h-19h',
            'categorias': ['Cosméticos', 'Perfumes', 'Skincare', 'Maquiagem'],
            'ativo': True
        },
        {
            'nome': 'Best Buy - International Drive',
            'endereco': '8250 International Dr, Orlando, FL 32819',
            'cidade': 'Orlando',
            'estado': 'FL',
            'pais': 'USA',
            'telefone': '+1 (407) 352-0000',
            'website': 'https://www.bestbuy.com',
            'horario_funcionamento': 'Seg-Dom: 10h-21h',
            'categorias': ['Eletrônicos', 'Computadores', 'Celulares', 'TVs', 'Áudio'],
            'ativo': True
        },
        {
            'nome': 'CVS Pharmacy - Disney Springs',
            'endereco': '1486 E Buena Vista Dr, Lake Buena Vista, FL 32830',
            'cidade': 'Lake Buena Vista',
            'estado': 'FL',
            'pais': 'USA',
            'telefone': '+1 (407) 828-0000',
            'website': 'https://www.cvs.com',
            'horario_funcionamento': 'Seg-Dom: 8h-22h',
            'categorias': ['Farmacia', 'Cosméticos', 'Suplementos', 'Cuidados Pessoais'],
            'ativo': True
        }
    ]
    
    created_count = 0
    for establishment_data in establishments:
        establishment, created = Estabelecimento.objects.get_or_create(
            nome=establishment_data['nome'],
            defaults=establishment_data
        )
        
        if created:
            created_count += 1
            print(f"✅ Criado: {establishment.nome}")
        else:
            print(f"⚠️  Já existe: {establishment.nome}")
    
    print(f"\n🎉 {created_count} estabelecimentos criados com sucesso!")
    print(f"📊 Total de estabelecimentos: {Estabelecimento.objects.count()}")
    
    return created_count

def main():
    """Função principal"""
    print("🏪 Adicionando estabelecimentos de teste...")
    
    try:
        created_count = create_test_establishments()
        
        print("\n" + "="*60)
        print("✅ ESTABELECIMENTOS DE TESTE CRIADOS!")
        print("="*60)
        print("\n📋 Estabelecimentos disponíveis:")
        
        for establishment in Estabelecimento.objects.all():
            print(f"   🏪 {establishment.nome} - {establishment.cidade}/{establishment.estado}")
        
        print(f"\n🎯 Agora os shoppers podem:")
        print("   ✅ Selecionar onde encontraram cada produto")
        print("   ✅ Especificar localização exata na loja")
        print("   ✅ Adicionar códigos de barras e SKUs")
        print("   ✅ Voltar ao local exato para comprar")
        
    except Exception as e:
        print(f"\n❌ Erro ao criar estabelecimentos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
