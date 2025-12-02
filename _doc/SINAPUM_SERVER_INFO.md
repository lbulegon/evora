# Informações do Servidor SinapUm - OpenMind AI

Este documento contém informações sobre o servidor SinapUm onde será hospedado o sistema OpenMind AI.

---

## Conexão SSH

**Host:** `69.169.102.84`  
**Usuário:** `root`  
**Porta:** `22` (padrão)

### Comando de Conexão

```bash
ssh root@69.169.102.84
```

### Autenticação

- **Método:** Senha
- **Senha:** Configurada no arquivo `.env` (não versionado)
- **Variáveis no `.env`:**
  ```bash
  SINAPUM_SSH_HOST=69.169.102.84
  SINAPUM_SSH_USER=root
  SINAPUM_SSH_PASSWORD=sua-senha-aqui
  SINAPUM_SSH_PORT=22
  ```
- **Nota:** O arquivo `.env` está no `.gitignore` e não será commitado. Use `environment_variables.example` como referência.

### Configuração Rápida

Para facilitar o acesso, você pode configurar um alias no `~/.ssh/config`:

```ssh-config
Host sinapum
    HostName 69.169.102.84
    User root
    Port 22
```

Depois, basta usar: `ssh sinapum`

---

## Informações do Sistema

**Hostname:** `sinapum`  
**Sistema Operacional:** Ubuntu 24.04 (minimal)  
**Último Login:** Mon Dec 1 22:18:38 2025

### Observações

- Sistema minimizado (minimal install)
- Rede configurada via `/etc/netplan/` usando `eth0` + DHCP
- Pode ser alterado para configuração estática se necessário

---

## Serviços e Aplicações

### OpenMind AI

**Status:** A implementar  
**URL Base:** A definir  
**Porta:** A definir  

---

## Configurações de Rede

### Netplan

Arquivo de configuração: `/etc/netplan/sample-netplan.txt`

Configuração atual:
- Interface: `eth0`
- Método: `dhcp`

Para configuração estática, ver: `/etc/netplan/sample-netplan.txt`

---

## Documentação Relacionada

- [`_doc/INTEGRACAO_OPENMIND_AI.md`](INTEGRACAO_OPENMIND_AI.md) - Visão geral da integração
- [`_doc/ESPECIFICACAO_API_OPENMIND_AI.md`](ESPECIFICACAO_API_OPENMIND_AI.md) - Especificação da API

---

## Configuração do Arquivo .env

As credenciais do servidor SinapUm devem ser configuradas no arquivo `.env` local:

1. **Copie o exemplo:**
   ```bash
   cp .env.local.example .env
   ```

2. **Edite o arquivo `.env`** e configure as variáveis:
   ```bash
   SINAPUM_SSH_HOST=69.169.102.84
   SINAPUM_SSH_USER=root
   SINAPUM_SSH_PASSWORD=Ljb#215195
   SINAPUM_SSH_PORT=22
   ```

3. **O arquivo `.env` está protegido** pelo `.gitignore` e não será commitado.

## Notas de Segurança

⚠️ **IMPORTANTE:**

- Credenciais sensíveis devem ser armazenadas no arquivo `.env` (não versionado)
- Nunca commitar senhas ou chaves privadas no repositório
- Use `environment_variables.example` como referência para todas as variáveis
- Usar autenticação por chave SSH quando possível (mais seguro)
- Considerar configurar firewall e acesso restrito

---

## Próximos Passos

1. ✅ Documentar informações do servidor
2. ⏳ Configurar autenticação por chave SSH (recomendado)
3. ⏳ Instalar dependências necessárias para OpenMind AI
4. ⏳ Configurar firewall e segurança
5. ⏳ Implementar endpoint da API conforme especificação

---

## Comandos Úteis

### Verificar Status do Sistema

```bash
# Status do sistema
systemctl status

# Espaço em disco
df -h

# Memória
free -h

# Processos
top
```

### Instalar Dependências

```bash
# Atualizar sistema
apt update && apt upgrade -y

# Instalar Python e ferramentas básicas
apt install -y python3 python3-pip git curl wget
```

### Configurar Firewall (UFW)

```bash
# Instalar UFW
apt install -y ufw

# Permitir SSH
ufw allow 22/tcp

# Permitir HTTP/HTTPS (quando configurado)
ufw allow 80/tcp
ufw allow 443/tcp

# Ativar firewall
ufw enable
```

---

**Última Atualização:** Dezembro 2025
