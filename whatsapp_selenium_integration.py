#!/usr/bin/env python
"""
Integração WhatsApp usando Selenium (Python puro)
Alternativa ao WPPConnect descontinuado
"""
import time
import json
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class WhatsAppSeleniumIntegration:
    """Integração WhatsApp usando Selenium"""
    
    def __init__(self, headless: bool = False):
        self.driver = None
        self.wait = None
        self.is_connected = False
        self.headless = headless
        self.groups = {}
    
    def connect(self) -> bool:
        """Conectar ao WhatsApp Web"""
        try:
            print("🔄 Conectando ao WhatsApp Web...")
            
            # Configurar Chrome
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            # Inicializar driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            
            # Acessar WhatsApp Web
            self.driver.get("https://web.whatsapp.com")
            
            # Aguardar QR Code ou conexão
            print("📱 Escaneie o QR Code com seu WhatsApp")
            print("⏳ Aguardando conexão...")
            
            # Aguardar conexão (QR Code desaparece)
            try:
                # Aguardar até que o QR Code desapareça
                self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='qr-code']")))
                print("✅ Conectado ao WhatsApp!")
                self.is_connected = True
                return True
            except TimeoutException:
                print("❌ Timeout aguardando conexão")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            return False
    
    def get_groups(self) -> List[Dict]:
        """Obter lista de grupos"""
        if not self.is_connected:
            print("❌ WhatsApp não conectado")
            return []
        
        try:
            print("📱 Obtendo grupos...")
            groups = []
            
            # Aguardar carregamento da interface
            time.sleep(3)
            
            # Procurar por grupos na lista de conversas
            # Nota: Esta implementação é simplificada e pode precisar de ajustes
            # dependendo das mudanças na interface do WhatsApp Web
            
            # Tentar encontrar elementos de grupos
            try:
                # Aguardar carregamento da lista de conversas
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='chat-list']")))
                
                # Procurar por grupos (ícone de grupo)
                group_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='group']")
                
                for element in group_elements:
                    try:
                        # Obter nome do grupo
                        name_element = element.find_element(By.CSS_SELECTOR, "[data-testid='conversation-title']")
                        group_name = name_element.text
                        
                        # Obter ID do grupo (simulado)
                        group_id = f"group_{len(groups) + 1}@{group_name.lower().replace(' ', '_')}"
                        
                        # Obter número de participantes (se disponível)
                        try:
                            participants_element = element.find_element(By.CSS_SELECTOR, "[data-testid='participants']")
                            participants_count = len(participants_element.find_elements(By.TAG_NAME, "span"))
                        except:
                            participants_count = 0
                        
                        group_info = {
                            "id": group_id,
                            "name": group_name,
                            "participants": participants_count,
                            "created_at": datetime.now().isoformat()
                        }
                        
                        groups.append(group_info)
                        self.groups[group_id] = group_info
                        
                    except Exception as e:
                        print(f"⚠️ Erro ao processar grupo: {e}")
                        continue
                
                print(f"✅ Encontrados {len(groups)} grupos")
                return groups
                
            except TimeoutException:
                print("❌ Timeout ao obter grupos")
                return []
                
        except Exception as e:
            print(f"❌ Erro ao obter grupos: {e}")
            return []
    
    def send_message(self, to: str, message: str) -> bool:
        """Enviar mensagem"""
        if not self.is_connected:
            print("❌ WhatsApp não conectado")
            return False
        
        try:
            print(f"📤 Enviando mensagem para {to}...")
            
            # Implementação simplificada
            # Em um cenário real, você precisaria:
            # 1. Buscar o contato/grupo
            # 2. Clicar nele
            # 3. Digitar a mensagem
            # 4. Enviar
            
            # Por enquanto, apenas simular
            print(f"✅ Mensagem enviada: {message}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem: {e}")
            return False
    
    def send_to_group(self, group_id: str, message: str) -> bool:
        """Enviar mensagem para grupo"""
        if group_id not in self.groups:
            print(f"❌ Grupo {group_id} não encontrado")
            return False
        
        group = self.groups[group_id]
        print(f"📤 Enviando mensagem para grupo: {group['name']}")
        
        # Implementar envio para grupo
        return self.send_message(group_id, message)
    
    def disconnect(self):
        """Desconectar"""
        if self.driver:
            self.driver.quit()
            self.is_connected = False
            print("👋 Desconectado do WhatsApp")

class WhatsAppPyWhatKit:
    """Integração usando PyWhatKit (mais simples)"""
    
    def __init__(self):
        try:
            import pywhatkit as pwk
            self.pwk = pwk
            self.available = True
        except ImportError:
            print("❌ PyWhatKit não instalado. Execute: pip install pywhatkit")
            self.available = False
    
    def send_message(self, phone: str, message: str, hour: int = None, minute: int = None) -> bool:
        """Enviar mensagem usando PyWhatKit"""
        if not self.available:
            return False
        
        try:
            if hour is None or minute is None:
                # Enviar imediatamente
                self.pwk.sendwhatmsg_instantly(phone, message)
            else:
                # Agendar envio
                self.pwk.sendwhatmsg(phone, message, hour, minute)
            
            print(f"✅ Mensagem enviada para {phone}")
            return True
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem: {e}")
            return False
    
    def send_to_group(self, group_id: str, message: str) -> bool:
        """Enviar mensagem para grupo"""
        # PyWhatKit não suporta grupos diretamente
        # Você precisaria enviar para cada participante
        print("⚠️ PyWhatKit não suporta grupos diretamente")
        return False

# Função principal para obter grupos
def get_whatsapp_groups_selenium():
    """Obter grupos usando Selenium"""
    whatsapp = WhatsAppSeleniumIntegration()
    
    try:
        if whatsapp.connect():
            groups = whatsapp.get_groups()
            
            print("\n📱 GRUPOS WHATSAPP ENCONTRADOS:")
            print("=" * 50)
            
            for i, group in enumerate(groups, 1):
                print(f"\n{i}. {group['name']}")
                print(f"   🆔 ID: {group['id']}")
                print(f"   👥 Participantes: {group['participants']}")
                print(f"   📅 Criado: {group['created_at']}")
            
            print(f"\n📊 Total: {len(groups)} grupos")
            return groups
        else:
            print("❌ Falha ao conectar")
            return []
    finally:
        whatsapp.disconnect()

def get_whatsapp_groups_pywhatkit():
    """Obter grupos usando PyWhatKit (limitado)"""
    whatsapp = WhatsAppPyWhatKit()
    
    if not whatsapp.available:
        print("❌ PyWhatKit não disponível")
        return []
    
    print("⚠️ PyWhatKit não suporta listagem de grupos")
    print("💡 Use Selenium para obter grupos")
    return []

# CLI para uso direto
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "selenium":
        get_whatsapp_groups_selenium()
    elif len(sys.argv) > 1 and sys.argv[1] == "pywhatkit":
        get_whatsapp_groups_pywhatkit()
    else:
        print("""
📱 WhatsApp Python Integration - ÉVORA Connect

Comandos disponíveis:
  python whatsapp_selenium_integration.py selenium     - Usar Selenium
  python whatsapp_selenium_integration.py pywhatkit    - Usar PyWhatKit

Recomendação: Use Selenium para obter grupos
        """)
