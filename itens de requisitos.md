# Requisitos VitrineZap

> **⚠️ IMPORTANTE:** Todos os requisitos devem ser implementados respeitando os princípios fundadores do Évora/VitrineZap definidos em `PROMPT_FUNDADOR_EVORA.md`
> 
> **Princípios fundamentais:**
> - Comprar é iniciar uma conversa, não clicar em um botão
> - O chat é a interface principal
> - No grupo nasce o desejo, no privado nasce o compromisso
> - Carrinho invisível, nunca forçar formulários
> - IA-Vendedor (humano), não IA-Bot (robótico)

## 1. Melhorar a velocidade de análise
- Implementar cache de análises similares
- Otimizar processamento de imagens (reduzir qualidade/resolução antes de enviar)
- Processar múltiplas imagens em paralelo
- Adicionar progresso visual durante análise

## 2. Adicionar preço e outras informações no cadastro
- ✅ Adicionar campo de preço no formulário de análise
- ✅ Permitir edição rápida de preço diretamente no cadastro
- ✅ Adicionar campos adicionais (desconto, estoque, etc.)
- Melhorar UX do formulário de edição

## 3. Fluxo de cadastro de estabelecimento
- Capturar localização GPS do usuário
- Integrar com Google Places API / Foursquare
- Buscar estabelecimentos próximos baseado na localização
- Permitir seleção de estabelecimento da lista
- Capturar fotografia do estabelecimento
- Auto-preenchimento de dados do estabelecimento selecionado

## 4. Comentários de voz no cadastro
- Adicionar gravação de áudio no formulário
- Integrar com API de transcrição (Whisper/Google Speech)
- Salvar comentários de voz vinculados ao produto
- Permitir reprodução de áudio no WhatsApp

## 5. Edição rápida de itens relevantes
- ✅ Adicionar edição inline de preço
- Edição rápida de outros campos (nome, marca, etc.)
- Salvar alterações sem recarregar página

## 6. Integração WhatsApp - Respostas de voz
- Permitir que shoppers respondam com áudio
- Transcrever áudio para texto quando necessário
- Enviar respostas via WhatsApp

## 7. O cadastro do estabelecimento deve pegar a localização
- Encontrar as informações do estabelecimento daquele endereço
- Gerar uma lista de escolhas dos estabelecimentos próximos para ser selecionado
- Ao selecionar o estabelecimento da lista gera o cadastro

## 8. Editar itens relevantes como preço direto no cadastro
- ✅ Tem que colocar para editar os itens relevantes como preço direto no cadastro
- Permitir edição rápida sem sair da página de cadastro

---

## Status de Implementação

- ✅ **Concluído**: Campo de preço adicionado e funcional
- ✅ **Concluído**: Campo de estoque adicionado
- ✅ **Concluído**: Preço preenchido automaticamente quando detectado pela IA
- ✅ **Concluído**: Preço e estoque salvos no JSON do produto
- 🔄 **Em Progresso**: Fluxo de cadastro de estabelecimento com geolocalização
- ⏳ **Pendente**: Comentários de voz
- ⏳ **Pendente**: Melhorias de velocidade de análise
- ⏳ **Pendente**: Integração com Google Places/Foursquare
- ⏳ **Pendente**: Edição rápida inline de outros campos

