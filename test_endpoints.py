#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar endpoints importantes do VitrineZap
"""
import requests
import sys

def test_endpoint(url, expected_status=200, description=""):
    """Testa um endpoint específico"""
    try:
        print(f"Testando: {description or url}")
        response = requests.get(url, timeout=10)
        
        if response.status_code == expected_status:
            print(f"  OK - Status {response.status_code}")
            return True
        else:
            print(f"  ERRO - Status {response.status_code} (esperado {expected_status})")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ERRO - {e}")
        return False

def main():
    """Testa endpoints principais"""
    
    # Definir base URL (local ou Railway)
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    else:
        base_url = "http://127.0.0.1:8002"  # Padrão local
    
    print(f"TESTANDO ENDPOINTS - {base_url}")
    print("=" * 50)
    
    # Lista de endpoints para testar
    endpoints = [
        ("/health/", 200, "Health Check"),
        ("/", 200, "Página Principal"),
        ("/admin/", 302, "Admin (redirect para login)"),
        ("/login/", 200, "Página de Login"),
        ("/cadastro/", 200, "Página de Cadastro"),
    ]
    
    # Testar cada endpoint
    results = []
    for path, expected_status, description in endpoints:
        url = base_url + path
        success = test_endpoint(url, expected_status, description)
        results.append(success)
    
    # Resumo
    print("\n" + "=" * 50)
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"RESUMO: {passed}/{total} endpoints OK")
    
    if failed > 0:
        print(f"AVISO: {failed} endpoints com problema")
        sys.exit(1)
    else:
        print("SUCESSO: Todos os endpoints funcionando!")
        sys.exit(0)

if __name__ == '__main__':
    main()
