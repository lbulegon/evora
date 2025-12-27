# Correções de Endereços - Core_SinapUm

## Resumo das Alterações

Após a reorganização do projeto SinapUm para Core_SinapUm (anteriormente MCP_SinapUm) e mudança da porta de `80` para `5000`, foram corrigidos todos os endereços e referências no projeto ÉVORA.

## Mudanças Realizadas

### 1. Porta do Servidor
- **Antes:** `8000` (ou `80` no sistema)
- **Depois:** `5000`
- **URL Base:** `http://69.169.102.84:5000`

### 2. Arquivos Corrigidos

#### Arquivos de Teste
- ✅ `test_imagem_sinapum.py` - Porta 8000 → 5000
- ✅ `test_openmind_server.py` - Porta 8000 → 5000
- ✅ `test_sistema_imagens.py` - Porta 8000 → 5000, atualizado comentários
- ✅ `test_url_builder.py` - Porta 8000 → 5000

#### Arquivos de Serviços
- ✅ `app_marketplace/services.py` - URL padrão 8001 → 5000
- ✅ `app_marketplace/utils.py` - URL padrão 8001 → 5000

#### Arquivos de Configuração
- ✅ `environment_variables.example` - OPENMIND_AI_URL atualizado para porta 5000
- ✅ Comentários atualizados de "SinapUm" para "Core_SinapUm" onde apropriado

### 3. URLs Atualizadas

#### Antes:
```
http://69.169.102.84:8000
http://69.169.102.84:8000/api/v1
http://127.0.0.1:8001
```

#### Depois:
```
http://69.169.102.84:5000
http://69.169.102.84:5000/api/v1
http://127.0.0.1:5000
```

### 4. Variáveis de Ambiente

Atualize a variável de ambiente `OPENMIND_AI_URL` no seu ambiente:

```bash
OPENMIND_AI_URL=http://69.169.102.84:5000/api/v1
```

### 5. Endpoints Principais

- **Health Check:** `http://69.169.102.84:5000/health`
- **API Docs:** `http://69.169.102.84:5000/docs`
- **Análise de Imagem:** `http://69.169.102.84:5000/api/v1/analyze-product-image`
- **Media (Imagens):** `http://69.169.102.84:5000/media/uploads/`

## Notas Importantes

1. **Arquivos de Documentação:** Os arquivos em `_doc/` e `openmind-ai-server/` ainda contêm referências à porta 8000, mas são apenas documentação. O código funcional está correto.

2. **Testes Locais:** Os testes que usam `localhost:8000` referem-se ao servidor Django do próprio projeto ÉVORA, não ao Core_SinapUm, então não precisam ser alterados.

3. **Railway/Produção:** Certifique-se de atualizar a variável de ambiente `OPENMIND_AI_URL` no Railway para apontar para a porta 5000.

## Verificação

Para verificar se as correções estão funcionando:

```bash
# Testar health check
curl http://69.169.102.84:5000/health

# Testar análise de imagem
curl -X POST http://69.169.102.84:5000/api/v1/analyze-product-image \
  -F "image=@test_image.jpg" \
  -F "language=pt-BR"
```

## Status

✅ **Todas as correções foram aplicadas nos arquivos principais do projeto ÉVORA.**

