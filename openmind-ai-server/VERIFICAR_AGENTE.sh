#!/bin/bash
# Script para verificar se o agente está funcionando corretamente
# Uso: ./VERIFICAR_AGENTE.sh [API_KEY]

set -e

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Obter API key
if [ -z "$1" ]; then
    if [ -f ".env" ]; then
        API_KEY=$(grep OPENMIND_AI_API_KEY .env | cut -d '=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
    else
        echo -e "${RED}❌ Erro: API key não fornecida e .env não encontrado${NC}"
        echo "Uso: ./VERIFICAR_AGENTE.sh [API_KEY]"
        exit 1
    fi
else
    API_KEY=$1
fi

BASE_URL="http://localhost:8000"
HEADER="Authorization: Bearer $API_KEY"

echo "🔍 Verificando agente ágnosto no SinapUm..."
echo ""

# Teste 1: Health Check
echo "1️⃣ Testando health check..."
if response=$(curl -s "$BASE_URL/health"); then
    echo -e "${GREEN}✅ Health check OK${NC}"
    echo "   Resposta: $response"
else
    echo -e "${RED}❌ Health check falhou${NC}"
    exit 1
fi

echo ""

# Teste 2: Listar papéis
echo "2️⃣ Testando listar papéis..."
if response=$(curl -s -H "$HEADER" "$BASE_URL/api/v1/agent/roles"); then
    if echo "$response" | grep -q "vendedor"; then
        echo -e "${GREEN}✅ Listar papéis OK${NC}"
        echo "   Resposta: $response"
    else
        echo -e "${RED}❌ Listar papéis falhou${NC}"
        echo "   Resposta: $response"
    fi
else
    echo -e "${RED}❌ Erro ao chamar endpoint${NC}"
fi

echo ""

# Teste 3: Listar capacidades
echo "3️⃣ Testando listar capacidades..."
if response=$(curl -s -H "$HEADER" "$BASE_URL/api/v1/agent/capabilities?role=vendedor"); then
    if echo "$response" | grep -q "add_to_cart"; then
        echo -e "${GREEN}✅ Listar capacidades OK${NC}"
        echo "   Resposta: $response"
    else
        echo -e "${RED}❌ Listar capacidades falhou${NC}"
        echo "   Resposta: $response"
    fi
else
    echo -e "${RED}❌ Erro ao chamar endpoint${NC}"
fi

echo ""

# Teste 4: Processar mensagem
echo "4️⃣ Testando processar mensagem..."
PAYLOAD='{
  "message": "Quero adicionar 2 unidades",
  "conversation_id": "PRIV-TEST-123",
  "user_phone": "+5511999999999",
  "user_name": "Teste",
  "is_group": false,
  "offer_id": "OFT-TEST-123",
  "language": "pt-BR",
  "agent_role": "vendedor",
  "metadata": {
    "produto_id": 1,
    "produto_nome": "Produto Teste",
    "preco": "89.90",
    "moeda": "BRL"
  }
}'

if response=$(curl -s -X POST "$BASE_URL/api/v1/process-message" \
    -H "$HEADER" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD"); then
    if echo "$response" | grep -q "success"; then
        echo -e "${GREEN}✅ Processar mensagem OK${NC}"
        echo "   Resposta: $response"
    else
        echo -e "${RED}❌ Processar mensagem falhou${NC}"
        echo "   Resposta: $response"
    fi
else
    echo -e "${RED}❌ Erro ao chamar endpoint${NC}"
fi

echo ""
echo -e "${GREEN}✅ Verificação concluída!${NC}"

