-- ============================================================================
-- Script SQL para excluir todos os registros da tabela app_marketplace_produtojson
-- ============================================================================
-- ATENÇÃO: Esta operação é IRREVERSÍVEL!
-- Recomenda-se fazer backup antes de executar:
--   pg_dump -t app_marketplace_produtojson database_name > backup_produtojson.sql
-- ============================================================================

-- Opção 1: DELETE (mais seguro, pode ser revertido com ROLLBACK se dentro de transação)
-- Recomendado para produção
DELETE FROM public.app_marketplace_produtojson;

-- Opção 2: TRUNCATE (mais rápido, não pode ser revertido, reseta auto-increment)
-- Use apenas se tiver certeza absoluta
-- TRUNCATE TABLE public.app_marketplace_produtojson;

-- Opção 3: TRUNCATE com CASCADE (remove também registros relacionados em outras tabelas)
-- Use com EXTREMA CAUTELA - pode deletar dados relacionados
-- TRUNCATE TABLE public.app_marketplace_produtojson CASCADE;

-- Opção 4: DELETE com confirmação de quantidade (recomendado para verificar antes)
-- Descomente para ver quantos registros serão deletados antes de executar:
-- SELECT COUNT(*) as total_registros FROM public.app_marketplace_produtojson;
-- DELETE FROM public.app_marketplace_produtojson;

-- ============================================================================
-- Verificação após exclusão
-- ============================================================================
-- Execute para confirmar que todos os registros foram deletados:
-- SELECT COUNT(*) as registros_restantes FROM public.app_marketplace_produtojson;
-- Deve retornar: 0
-- ============================================================================

