#!/usr/bin/env python
"""
Script de Teste Completo - Sistema ÉVORA
=========================================
Testa todos os componentes do sistema para verificar se está funcionando.
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

import json
from datetime import datetime
from django.db import connection
from django.core.management import call_command
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Model

# Importar modelos
from app_marketplace.models import (
    # Modelos base
    Empresa, Categoria, ProdutoJSON, Cliente, PersonalShopper, AddressKeeper,
    # Modelos KMN
    Pacote, MovimentoPacote, FotoPacote, OpcaoEnvio,
    # Modelos pagamento
    PagamentoIntent, PagamentoSplit, IntentCompra, PedidoPacote,
    # Modelos WhatsApp conversacional
    OfertaProduto, IntencaoSocial, ConversaContextualizada, CarrinhoInvisivel,
    # Modelos WhatsApp base
    WhatsappGroup, WhatsappParticipant, WhatsappConversation
)

# Importar serviços
from app_marketplace.whatsapp_flow_engine import WhatsAppFlowEngine
from app_whatsapp_integration.evolution_service import EvolutionAPIService

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

# Resultados dos testes
results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def test_result(name, passed, message="", warning=False):
    if passed:
        print_success(f"{name}: {message}")
        results['passed'].append(name)
    elif warning:
        print_warning(f"{name}: {message}")
        results['warnings'].append(name)
    else:
        print_error(f"{name}: {message}")
        results['failed'].append(name)

# ============================================================================
# TESTE 1: Estrutura e Configuração
# ============================================================================

def test_estrutura():
    print_header("TESTE 1: Estrutura e Configuração")
    
    # Verificar Django settings
    try:
        assert hasattr(settings, 'SECRET_KEY'), "SECRET_KEY não configurado"
        assert settings.SECRET_KEY != 'django-insecure-...', "SECRET_KEY está usando valor padrão inseguro"
        test_result("Django Settings", True, "Configurado corretamente")
    except AssertionError as e:
        test_result("Django Settings", False, str(e))
    
    # Verificar banco de dados
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            test_result("Conexão Banco de Dados", True, "Conectado com sucesso")
    except Exception as e:
        test_result("Conexão Banco de Dados", False, str(e))
    
    # Verificar variáveis de ambiente
    env_vars = {
        'OPENMIND_AI_URL': settings.OPENMIND_AI_URL,
        'EVOLUTION_API_URL': settings.EVOLUTION_API_URL,
        'EVOLUTION_API_KEY': settings.EVOLUTION_API_KEY,
    }
    
    for var_name, var_value in env_vars.items():
        if var_value:
            test_result(f"Variável {var_name}", True, f"Configurada: {var_value[:50]}...")
        else:
            test_result(f"Variável {var_name}", False, "Não configurada", warning=True)

# ============================================================================
# TESTE 2: Modelos Django
# ============================================================================

def test_modelos():
    print_header("TESTE 2: Modelos Django")
    
    modelos_para_testar = [
        # Modelos base
        ('Empresa', Empresa),
        ('Categoria', Categoria),
        ('ProdutoJSON', ProdutoJSON),
        ('Cliente', Cliente),
        ('PersonalShopper', PersonalShopper),
        ('AddressKeeper', AddressKeeper),
        # Modelos KMN
        ('Pacote', Pacote),
        ('MovimentoPacote', MovimentoPacote),
        ('FotoPacote', FotoPacote),
        ('OpcaoEnvio', OpcaoEnvio),
        # Modelos pagamento
        ('PagamentoIntent', PagamentoIntent),
        ('PagamentoSplit', PagamentoSplit),
        ('IntentCompra', IntentCompra),
        ('PedidoPacote', PedidoPacote),
        # Modelos WhatsApp conversacional
        ('OfertaProduto', OfertaProduto),
        ('IntencaoSocial', IntencaoSocial),
        ('ConversaContextualizada', ConversaContextualizada),
        ('CarrinhoInvisivel', CarrinhoInvisivel),
        # Modelos WhatsApp base
        ('WhatsappGroup', WhatsappGroup),
        ('WhatsappParticipant', WhatsappParticipant),
        ('WhatsappConversation', WhatsappConversation),
    ]
    
    for nome, modelo in modelos_para_testar:
        try:
            # Verificar se modelo existe
            assert issubclass(modelo, Model), f"{nome} não é um modelo Django"
            
            # Verificar se tem tabela no banco
            if modelo._meta.db_table in connection.introspection.table_names():
                test_result(f"Modelo {nome}", True, "Tabela existe no banco")
            else:
                test_result(f"Modelo {nome}", False, "Tabela não existe no banco (migração pendente?)", warning=True)
        except Exception as e:
            test_result(f"Modelo {nome}", False, str(e))

# ============================================================================
# TESTE 3: Migrações
# ============================================================================

def test_migracoes():
    print_header("TESTE 3: Migrações")
    
    try:
        # Verificar migrações pendentes
        from io import StringIO
        from django.core.management import call_command
        
        output = StringIO()
        call_command('showmigrations', 'app_marketplace', stdout=output, no_color=True)
        output_str = output.getvalue()
        
        # Contar migrações aplicadas
        applied = output_str.count('[X]')
        pending = output_str.count('[ ]')
        
        if pending == 0:
            test_result("Migrações app_marketplace", True, f"Todas aplicadas ({applied} migrações)")
        else:
            test_result("Migrações app_marketplace", False, f"{pending} migrações pendentes, {applied} aplicadas", warning=True)
            print_info("Execute: python manage.py migrate app_marketplace")
        
        # Verificar migrações do app_whatsapp_integration
        output2 = StringIO()
        call_command('showmigrations', 'app_whatsapp_integration', stdout=output2, no_color=True)
        output_str2 = output2.getvalue()
        
        applied2 = output_str2.count('[X]')
        pending2 = output_str2.count('[ ]')
        
        if pending2 == 0:
            test_result("Migrações app_whatsapp_integration", True, f"Todas aplicadas ({applied2} migrações)")
        else:
            test_result("Migrações app_whatsapp_integration", False, f"{pending2} migrações pendentes", warning=True)
    
    except Exception as e:
        test_result("Verificação de Migrações", False, str(e))

# ============================================================================
# TESTE 4: Serviços e Engines
# ============================================================================

def test_servicos():
    print_header("TESTE 4: Serviços e Engines")
    
    # Testar WhatsAppFlowEngine
    try:
        engine = WhatsAppFlowEngine()
        assert engine is not None, "WhatsAppFlowEngine não foi instanciado"
        assert hasattr(engine, 'evolution_service'), "WhatsAppFlowEngine não tem evolution_service"
        test_result("WhatsAppFlowEngine", True, "Instanciado corretamente")
    except Exception as e:
        test_result("WhatsAppFlowEngine", False, str(e))
    
    # Testar EvolutionAPIService
    try:
        service = EvolutionAPIService()
        assert service is not None, "EvolutionAPIService não foi instanciado"
        test_result("EvolutionAPIService", True, "Instanciado corretamente")
    except Exception as e:
        test_result("EvolutionAPIService", False, str(e))
    
    # Verificar métodos principais do WhatsAppFlowEngine
    try:
        engine = WhatsAppFlowEngine()
        metodos_necessarios = [
            'processar_mensagem_grupo',
            'processar_mensagem_privada',
            'iniciar_click_to_chat',  # Nome correto do método
            '_identificar_oferta_na_mensagem',
            '_criar_intencao_social',
        ]
        
        for metodo in metodos_necessarios:
            if hasattr(engine, metodo):
                test_result(f"Método {metodo}", True, "Existe")
            else:
                test_result(f"Método {metodo}", False, "Não encontrado")
    except Exception as e:
        test_result("Métodos WhatsAppFlowEngine", False, str(e))

# ============================================================================
# TESTE 5: Integrações Externas
# ============================================================================

def test_integracoes():
    print_header("TESTE 5: Integrações Externas")
    
    import requests
    
    # Testar SinapUm (OpenMind AI)
    try:
        url = settings.OPENMIND_AI_URL
        if url:
            # Fazer requisição simples para verificar se está acessível
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    test_result("SinapUm (OpenMind AI)", True, "Servidor acessível")
                else:
                    test_result("SinapUm (OpenMind AI)", False, f"Resposta HTTP {response.status_code}", warning=True)
            except requests.exceptions.RequestException as e:
                test_result("SinapUm (OpenMind AI)", False, f"Não acessível: {str(e)[:50]}", warning=True)
        else:
            test_result("SinapUm (OpenMind AI)", False, "URL não configurada", warning=True)
    except Exception as e:
        test_result("SinapUm (OpenMind AI)", False, str(e))
    
    # Testar Evolution API
    try:
        url = settings.EVOLUTION_API_URL
        if url:
            try:
                # Tentar acessar endpoint de health/status
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code in [200, 404]:  # 404 pode ser normal se não tiver endpoint health
                    test_result("Evolution API", True, "Servidor acessível")
                else:
                    test_result("Evolution API", False, f"Resposta HTTP {response.status_code}", warning=True)
            except requests.exceptions.RequestException as e:
                test_result("Evolution API", False, f"Não acessível: {str(e)[:50]}", warning=True)
        else:
            test_result("Evolution API", False, "URL não configurada", warning=True)
    except Exception as e:
        test_result("Evolution API", False, str(e))

# ============================================================================
# TESTE 6: Validação de Campos Críticos
# ============================================================================

def test_campos_criticos():
    print_header("TESTE 6: Validação de Campos Críticos")
    
    # Verificar campos obrigatórios dos modelos principais
    modelos_campos = {
        'OfertaProduto': ['oferta_id', 'produto', 'grupo'],
        'IntencaoSocial': ['oferta', 'participante', 'tipo'],
        'ConversaContextualizada': ['oferta', 'participante', 'conversa'],
        'CarrinhoInvisivel': ['conversa_contextualizada', 'itens'],
        'Pacote': ['address_keeper', 'status'],  # Campo correto é address_keeper
        'AddressKeeper': ['user'],
        'PersonalShopper': ['user'],
    }
    
    for nome_modelo, campos in modelos_campos.items():
        try:
            # Importar modelo dinamicamente
            modelo = globals().get(nome_modelo)
            if modelo:
                for campo in campos:
                    if hasattr(modelo, campo):
                        test_result(f"{nome_modelo}.{campo}", True, "Campo existe")
                    else:
                        test_result(f"{nome_modelo}.{campo}", False, "Campo não encontrado")
        except Exception as e:
            test_result(f"Validação {nome_modelo}", False, str(e))

# ============================================================================
# TESTE 7: Verificar Problemas Conhecidos
# ============================================================================

def test_problemas_conhecidos():
    print_header("TESTE 7: Verificar Problemas Conhecidos")
    
    # Verificar se comandos estão bloqueados no grupo
    try:
        from app_marketplace.whatsapp_views import handle_general_intent
        import inspect
        
        # Verificar se função detecta tipo de chat
        source = inspect.getsource(handle_general_intent)
        
        # Verificar se há validação de grupo vs privado
        if '@g.us' in source or 'grupo' in source.lower() or 'group' in source.lower():
            # Verificar se há bloqueio
            if 'ADD_TO_CART' in source and 'PAY' in source:
                # Verificar se há validação antes de processar
                if 'if' in source and ('@c.us' in source or 'privado' in source.lower() or 'private' in source.lower()):
                    test_result("Bloqueio comandos no grupo", True, "Validação implementada")
                else:
                    test_result("Bloqueio comandos no grupo", False, "Comandos podem funcionar no grupo", warning=True)
            else:
                test_result("Bloqueio comandos no grupo", False, "Comandos não encontrados no código")
        else:
            test_result("Bloqueio comandos no grupo", False, "Não há detecção de tipo de chat", warning=True)
    except Exception as e:
        test_result("Bloqueio comandos no grupo", False, f"Erro ao verificar: {str(e)}", warning=True)

# ============================================================================
# RELATÓRIO FINAL
# ============================================================================

def gerar_relatorio():
    print_header("RELATÓRIO FINAL")
    
    total = len(results['passed']) + len(results['failed']) + len(results['warnings'])
    pass_rate = (len(results['passed']) / total * 100) if total > 0 else 0
    
    print(f"\n{Colors.BOLD}Estatísticas:{Colors.RESET}")
    print(f"  ✅ Testes Passados: {Colors.GREEN}{len(results['passed'])}{Colors.RESET}")
    print(f"  ❌ Testes Falhados: {Colors.RED}{len(results['failed'])}{Colors.RESET}")
    print(f"  ⚠️  Avisos: {Colors.YELLOW}{len(results['warnings'])}{Colors.RESET}")
    print(f"  📊 Taxa de Sucesso: {Colors.BOLD}{pass_rate:.1f}%{Colors.RESET}")
    
    if results['failed']:
        print(f"\n{Colors.RED}{Colors.BOLD}Testes Falhados:{Colors.RESET}")
        for test in results['failed']:
            print(f"  ❌ {test}")
    
    if results['warnings']:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}Avisos:{Colors.RESET}")
        for test in results['warnings']:
            print(f"  ⚠️  {test}")
    
    print(f"\n{Colors.BOLD}Status Geral:{Colors.RESET}")
    if len(results['failed']) == 0 and len(results['warnings']) == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ SISTEMA TOTALMENTE FUNCIONAL!{Colors.RESET}")
    elif len(results['failed']) == 0:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  SISTEMA FUNCIONAL COM AVISOS{Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ SISTEMA COM PROBLEMAS CRÍTICOS{Colors.RESET}")
    
    # Salvar relatório em arquivo
    relatorio_file = BASE_DIR / 'relatorio_testes.json'
    relatorio_data = {
        'data': datetime.now().isoformat(),
        'estatisticas': {
            'passados': len(results['passed']),
            'falhados': len(results['failed']),
            'avisos': len(results['warnings']),
            'taxa_sucesso': pass_rate
        },
        'testes_passados': results['passed'],
        'testes_falhados': results['failed'],
        'testes_avisos': results['warnings']
    }
    
    with open(relatorio_file, 'w', encoding='utf-8') as f:
        json.dump(relatorio_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{Colors.BLUE}Relatório salvo em: {relatorio_file}{Colors.RESET}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("="*60)
    print("  TESTE COMPLETO DO SISTEMA ÉVORA")
    print("="*60)
    print(f"{Colors.RESET}")
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        test_estrutura()
        test_modelos()
        test_migracoes()
        test_servicos()
        test_integracoes()
        test_campos_criticos()
        test_problemas_conhecidos()
        gerar_relatorio()
    except Exception as e:
        print_error(f"Erro crítico durante os testes: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Exit code baseado nos resultados
    if len(results['failed']) > 0:
        sys.exit(1)
    elif len(results['warnings']) > 0:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()

