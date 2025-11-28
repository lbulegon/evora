#!/usr/bin/env node
/**
 * Integração WhatsApp usando Baileys (alternativa ao WPPConnect)
 * Mais estável e mantido ativamente
 */

const { default: makeWASocket, DisconnectReason, useMultiFileAuthState } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const fs = require('fs');
const path = require('path');

class WhatsAppBaileysIntegration {
    constructor() {
        this.sock = null;
        this.authDir = './whatsapp_auth';
        this.isConnected = false;
    }

    async connect() {
        try {
            console.log('🔄 Conectando ao WhatsApp via Baileys...');
            
            // Criar diretório de autenticação se não existir
            if (!fs.existsSync(this.authDir)) {
                fs.mkdirSync(this.authDir, { recursive: true });
            }

            const { state, saveCreds } = await useMultiFileAuthState(this.authDir);
            
            this.sock = makeWASocket({
                auth: state,
                printQRInTerminal: true,
                browser: ['ÉVORA Connect', 'Chrome', '1.0.0'],
                defaultQueryTimeoutMs: 60 * 1000,
            });

            // Salvar credenciais quando necessário
            this.sock.ev.on('creds.update', saveCreds);

            // Gerenciar conexão
            this.sock.ev.on('connection.update', (update) => {
                const { connection, lastDisconnect, qr } = update;
                
                if (qr) {
                    console.log('📱 Escaneie o QR Code com seu WhatsApp');
                }
                
                if (connection === 'close') {
                    const shouldReconnect = (lastDisconnect?.error instanceof Boom)?.output?.statusCode !== DisconnectReason.loggedOut;
                    console.log('❌ Conexão fechada:', lastDisconnect?.error);
                    
                    if (shouldReconnect) {
                        console.log('🔄 Reconectando...');
                        this.connect();
                    }
                } else if (connection === 'open') {
                    console.log('✅ Conectado ao WhatsApp!');
                    this.isConnected = true;
                }
            });

            // Gerenciar mensagens recebidas
            this.sock.ev.on('messages.upsert', async (m) => {
                const msg = m.messages[0];
                if (!msg.key.fromMe && m.type === 'notify') {
                    console.log('📨 Nova mensagem recebida:', msg.message);
                    await this.handleIncomingMessage(msg);
                }
            });

            return true;
        } catch (error) {
            console.error('❌ Erro ao conectar:', error);
            return false;
        }
    }

    async getGroups() {
        if (!this.sock || !this.isConnected) {
            throw new Error('WhatsApp não conectado');
        }

        try {
            const groups = await this.sock.groupFetchAllParticipating();
            const groupList = [];

            for (const [id, group] of Object.entries(groups)) {
                groupList.push({
                    id: id,
                    name: group.subject,
                    participants: group.participants.length,
                    description: group.desc || '',
                    isAdmin: group.participants.some(p => p.admin === 'admin'),
                    createdAt: new Date(group.creation * 1000)
                });
            }

            return groupList;
        } catch (error) {
            console.error('❌ Erro ao obter grupos:', error);
            throw error;
        }
    }

    async sendMessage(to, message) {
        if (!this.sock || !this.isConnected) {
            throw new Error('WhatsApp não conectado');
        }

        try {
            await this.sock.sendMessage(to, { text: message });
            console.log(`✅ Mensagem enviada para ${to}`);
            return true;
        } catch (error) {
            console.error('❌ Erro ao enviar mensagem:', error);
            throw error;
        }
    }

    async sendMessageToGroup(groupId, message) {
        return await this.sendMessage(groupId, message);
    }

    async handleIncomingMessage(msg) {
        // Implementar lógica para processar mensagens recebidas
        console.log('📨 Processando mensagem:', {
            from: msg.key.remoteJid,
            message: msg.message
        });
        
        // Aqui você pode implementar:
        // - Detecção de comandos
        // - Processamento de pedidos
        // - Respostas automáticas
        // - Integração com ÉVORA
    }

    async disconnect() {
        if (this.sock) {
            await this.sock.logout();
            this.isConnected = false;
            console.log('👋 Desconectado do WhatsApp');
        }
    }
}

// Função para obter Chat IDs dos grupos
async function getWhatsAppGroups() {
    const whatsapp = new WhatsAppBaileysIntegration();
    
    try {
        await whatsapp.connect();
        
        // Aguardar conexão
        await new Promise(resolve => {
            const checkConnection = setInterval(() => {
                if (whatsapp.isConnected) {
                    clearInterval(checkConnection);
                    resolve();
                }
            }, 1000);
        });
        
        console.log('\n📱 GRUPOS WHATSAPP DISPONÍVEIS:');
        console.log('=' * 50);
        
        const groups = await whatsapp.getGroups();
        
        groups.forEach((group, index) => {
            console.log(`\n${index + 1}. ${group.name}`);
            console.log(`   🆔 Chat ID: ${group.id}`);
            console.log(`   👥 Participantes: ${group.participants}`);
            console.log(`   📅 Criado em: ${group.createdAt.toLocaleDateString()}`);
        });
        
        console.log(`\n📊 Total de grupos: ${groups.length}`);
        
        return groups;
        
    } catch (error) {
        console.error('❌ Erro:', error);
    } finally {
        await whatsapp.disconnect();
    }
}

// Função para enviar mensagem de teste
async function sendTestMessage(groupId, message) {
    const whatsapp = new WhatsAppBaileysIntegration();
    
    try {
        await whatsapp.connect();
        
        // Aguardar conexão
        await new Promise(resolve => {
            const checkConnection = setInterval(() => {
                if (whatsapp.isConnected) {
                    clearInterval(checkConnection);
                    resolve();
                }
            }, 1000);
        });
        
        await whatsapp.sendMessageToGroup(groupId, message);
        console.log('✅ Mensagem de teste enviada!');
        
    } catch (error) {
        console.error('❌ Erro:', error);
    } finally {
        await whatsapp.disconnect();
    }
}

// CLI para uso direto
if (require.main === module) {
    const command = process.argv[2];
    
    if (command === 'groups') {
        getWhatsAppGroups();
    } else if (command === 'send') {
        const groupId = process.argv[3];
        const message = process.argv[4] || 'Teste do ÉVORA Connect';
        sendTestMessage(groupId, message);
    } else {
        console.log(`
📱 WhatsApp Baileys Integration - ÉVORA Connect

Comandos disponíveis:
  node whatsapp_baileys_integration.js groups     - Listar grupos
  node whatsapp_baileys_integration.js send <id> <msg> - Enviar mensagem

Exemplos:
  node whatsapp_baileys_integration.js groups
  node whatsapp_baileys_integration.js send "120363123456789012@g.us" "Olá grupo!"
        `);
    }
}

module.exports = WhatsAppBaileysIntegration;
