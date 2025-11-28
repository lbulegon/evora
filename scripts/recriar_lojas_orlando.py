#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para recriar lojas de Orlando que foram perdidas na unificação.
Execute este script se os dados de Estabelecimento (Orlando) foram perdidos.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from app_marketplace.models import Empresa

def recriar_lojas_orlando():
    """
    Recria lojas de Orlando como Empresas.
    Lista de lojas comuns em Orlando/FL.
    """
    print("Recriando lojas de Orlando...")
    print("=" * 50)
    
    lojas_orlando = [
        {
            'nome': 'Walmart Supercenter',
            'cidade': 'Orlando',
            'estado': 'FL',
            'pais': 'USA',
            'endereco': 'Multiple locations in Orlando, FL',
            'telefone': '+1 (407) XXX-XXXX',
            'website': 'https://www.walmart.com',
            'horario_funcionamento': 'Mon-Sun: 6:00 AM - 12:00 AM',
            'categorias': ['Eletrônicos', 'Roupas', 'Casa', 'Alimentos'],
            'latitude': 28.5383,
            'longitude': -81.3792,
        },
        {
            'nome': 'Target',
            'cidade': 'Orlando',
            'estado': 'FL',
            'pais': 'USA',
            'endereco': 'Multiple locations in Orlando, FL',
            'telefone': '+1 (407) XXX-XXXX',
            'website': 'https://www.target.com',
            'horario_funcionamento': 'Mon-Sun: 8:00 AM - 10:00 PM',
            'categorias': ['Eletrônicos', 'Roupas', 'Casa', 'Beleza'],
            'latitude': 28.5383,
            'longitude': -81.3792,
        },
        {
            'nome': 'Best Buy',
            'cidade': 'Orlando',
            'estado': 'FL',
            'pais': 'USA',
            'endereco': 'Multiple locations in Orlando, FL',
            'telefone': '+1 (407) XXX-XXXX',
            'website': 'https://www.bestbuy.com',
            'horario_funcionamento': 'Mon-Sun: 10:00 AM - 9:00 PM',
            'categorias': ['Eletrônicos', 'Computadores', 'Celulares'],
            'latitude': 28.5383,
            'longitude': -81.3792,
        },
        {
            'nome': 'Macy\'s',
            'cidade': 'Orlando',
            'estado': 'FL',
            'pais': 'USA',
            'endereco': 'Multiple locations in Orlando, FL',
            'telefone': '+1 (407) XXX-XXXX',
            'website': 'https://www.macys.com',
            'horario_funcionamento': 'Mon-Sat: 10:00 AM - 9:00 PM, Sun: 11:00 AM - 7:00 PM',
            'categorias': ['Roupas', 'Calçados', 'Acessórios', 'Beleza'],
            'latitude': 28.5383,
            'longitude': -81.3792,
        },
        {
            'nome': 'Nike Store',
            'cidade': 'Orlando',
            'estado': 'FL',
            'pais': 'USA',
            'endereco': 'Multiple locations in Orlando, FL',
            'telefone': '+1 (407) XXX-XXXX',
            'website': 'https://www.nike.com',
            'horario_funcionamento': 'Mon-Sat: 10:00 AM - 9:00 PM, Sun: 11:00 AM - 7:00 PM',
            'categorias': ['Esportes', 'Roupas', 'Calçados'],
            'latitude': 28.5383,
            'longitude': -81.3792,
        },
        {
            'nome': 'CVS Pharmacy',
            'cidade': 'Orlando',
            'estado': 'FL',
            'pais': 'USA',
            'endereco': 'Multiple locations in Orlando, FL',
            'telefone': '+1 (407) XXX-XXXX',
            'website': 'https://www.cvs.com',
            'horario_funcionamento': 'Mon-Sun: 8:00 AM - 10:00 PM',
            'categorias': ['Farmácia', 'Beleza', 'Saúde'],
            'latitude': 28.5383,
            'longitude': -81.3792,
        },
        {
            'nome': 'Walgreens',
            'cidade': 'Orlando',
            'estado': 'FL',
            'pais': 'USA',
            'endereco': 'Multiple locations in Orlando, FL',
            'telefone': '+1 (407) XXX-XXXX',
            'website': 'https://www.walgreens.com',
            'horario_funcionamento': 'Mon-Sun: 8:00 AM - 10:00 PM',
            'categorias': ['Farmácia', 'Beleza', 'Saúde'],
            'latitude': 28.5383,
            'longitude': -81.3792,
        },
        {
            'nome': 'Ross Dress for Less',
            'cidade': 'Orlando',
            'estado': 'FL',
            'pais': 'USA',
            'endereco': 'Multiple locations in Orlando, FL',
            'telefone': '+1 (407) XXX-XXXX',
            'website': 'https://www.rossstores.com',
            'horario_funcionamento': 'Mon-Sat: 9:00 AM - 9:30 PM, Sun: 10:00 AM - 8:00 PM',
            'categorias': ['Roupas', 'Calçados', 'Acessórios', 'Casa'],
            'latitude': 28.5383,
            'longitude': -81.3792,
        },
    ]
    
    criadas = 0
    for loja in lojas_orlando:
        empresa, created = Empresa.objects.get_or_create(
            nome=loja['nome'],
            cidade=loja['cidade'],
            estado=loja['estado'],
            defaults={
                'pais': loja['pais'],
                'endereco': loja['endereco'],
                'telefone': loja['telefone'],
                'website': loja['website'],
                'horario_funcionamento': loja['horario_funcionamento'],
                'categorias': loja['categorias'],
                'latitude': loja['latitude'],
                'longitude': loja['longitude'],
                'ativo': True,
                'email': f"contato@{loja['nome'].lower().replace(' ', '').replace('\'', '')}.com",
            }
        )
        if created:
            criadas += 1
            print(f"  OK Criada: {loja['nome']} - {loja['cidade']}/{loja['estado']}")
        else:
            print(f"  -- Ja existe: {loja['nome']} - {loja['cidade']}/{loja['estado']}")
    
    print(f"\nOK Concluido: {criadas} loja(s) de Orlando criada(s)")
    print(f"Total de empresas em Orlando: {Empresa.objects.filter(cidade='Orlando', estado='FL').count()}")


if __name__ == '__main__':
    recriar_lojas_orlando()



