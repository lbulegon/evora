# 🎯 MVP Riviera - ÉVORA Connect (16/12)

## Objetivo
MVP funcional para testar compras durante a viagem à Riviera (México).

**Foco:** Operação do Shopper e Clientes
**Não necessário:** KMN, TrustLine, funcionalidades avançadas

---

## ✅ Funcionalidades Implementadas

### 1. Criação de Grupo WhatsApp ✅
- View `create_group` funcional
- API endpoint: `/api/whatsapp/groups/create/`
- Interface no dashboard do shopper
- Vinculação ao owner (shopper)

### 2. Gestão de Posts (Shopper) ✅
- **Criar Post:** Modal com formulário completo
- **Editar Post:** Edição de todos os campos
- **Deletar Post:** Confirmação e remoção
- **Listar Posts:** Grid visual com cards
- **Upload de Imagens:** Múltiplas imagens por post
- **Campos:** Nome, descrição, preço, moeda, marca, categoria, disponibilidade, destaque

**Localização:** `/shopper/groups/<group_id>/` → Aba "Produtos"

### 3. Captura de Imagens ✅
- Modelo `PostScreenshot` criado
- Upload de screenshot via interface
- Armazenamento em `/media/screenshots/posts/`
- Visualização de screenshots capturados
- Deletar screenshots

**API:**
- `POST /api/whatsapp/groups/<group_id>/products/<product_id>/screenshots/capture/`
- `GET /api/whatsapp/groups/<group_id>/products/<product_id>/screenshots/`
- `DELETE /api/whatsapp/groups/<group_id>/products/<product_id>/screenshots/<screenshot_id>/delete/`

### 4. Interface Cliente (Ver Produtos e Fazer Pedidos) ✅
- Listagem de produtos disponíveis
- Filtros: busca, categoria, grupo
- Visualização em cards
- Botão "Adicionar ao Carrinho" → Cria pedido
- Paginação

**Localização:** `/client/products/`

**API:**
- `POST /api/client/orders/create/` - Criar pedido

---

## 🔄 Fluxo Completo MVP

### Shopper:
1. Acessa `/shopper/groups/`
2. Cria ou seleciona grupo
3. Vai para aba "Produtos"
4. Clica em "Criar Novo Post"
5. Preenche dados e faz upload de imagens
6. Salva post
7. (Opcional) Captura screenshot do post

### Cliente:
1. Acessa `/client/products/`
2. Vê lista de produtos disponíveis
3. Filtra por busca/categoria/grupo
4. Clica em "Adicionar ao Carrinho"
5. Informa quantidade
6. Pedido é criado automaticamente

---

## 📁 Arquivos Criados/Modificados

### Models:
- `PostScreenshot` - Captura de screenshots

### Views:
- `get_product` - Buscar produto (edição)
- `update_product` - Atualizar post
- `delete_product` - Deletar post
- `capture_post_screenshot` - Capturar screenshot
- `get_post_screenshots` - Listar screenshots
- `delete_screenshot` - Deletar screenshot
- `client_products` - Listar produtos para cliente
- `create_whatsapp_order` - Criar pedido

### Templates:
- `client_products.html` - Interface cliente (NOVO)
- `shopper_group_detail.html` - Aba produtos atualizada

### URLs:
- `/api/whatsapp/groups/<group_id>/products/<product_id>/`
- `/api/whatsapp/groups/<group_id>/products/<product_id>/update/`
- `/api/whatsapp/groups/<group_id>/products/<product_id>/delete/`
- `/api/whatsapp/groups/<group_id>/products/<product_id>/screenshots/`
- `/api/whatsapp/groups/<group_id>/products/<product_id>/screenshots/capture/`
- `/api/whatsapp/groups/<group_id>/products/<product_id>/screenshots/<screenshot_id>/delete/`
- `/client/products/`
- `/api/client/orders/create/`

---

## 🚀 Próximos Passos (Opcional)

1. **Melhorias de UX:**
   - Carrinho de compras (múltiplos produtos)
   - Confirmação visual de pedido criado
   - Notificações

2. **Funcionalidades Adicionais:**
   - Edição de screenshots
   - Galeria de screenshots
   - Compartilhamento de posts

3. **Testes:**
   - Testar fluxo completo
   - Validar upload de imagens
   - Testar criação de pedidos

---

## ⚠️ Notas Importantes

- **KMN e TrustLine:** Funcionalidades desabilitadas/ignoradas no MVP
- **Foco:** Operação básica de shopper e clientes
- **Simplicidade:** Interface direta e objetiva
- **Teste:** Pronto para testar na viagem à Riviera

---

## 📝 Checklist Final

- [x] Criação de grupo funcional
- [x] Gestão completa de posts (CRUD)
- [x] Upload de imagens
- [x] Captura de screenshots
- [x] Interface cliente ver produtos
- [x] Cliente fazer pedidos
- [ ] Testar fluxo completo
- [ ] Ajustes finais

**Status:** ✅ MVP Pronto para Teste!

