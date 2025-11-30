-- Script SQL para tornar o campo message_id opcional na tabela app_marketplace_whatsappproduct
-- Execute este script diretamente no banco de dados do Railway se a migration não puder ser aplicada

-- 1. Primeiro, permitir NULL no campo message_id
ALTER TABLE app_marketplace_whatsappproduct 
ALTER COLUMN message_id DROP NOT NULL;

-- 2. Verificar se foi aplicado corretamente
-- SELECT column_name, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'app_marketplace_whatsappproduct' 
-- AND column_name = 'message_id';


