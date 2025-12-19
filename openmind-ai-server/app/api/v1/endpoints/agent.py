"""
Endpoint para Agente Ágnosto - Processamento de Mensagens WhatsApp
====================================================================

Endpoint que recebe mensagens do WhatsApp e processa usando agentes ágnostos.
Integra com Django Évora e Evolution API.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.core.security import verify_api_key
from app.core.agnostic_agent import (
    AgentFactory, AgentRole, AgentContext, AgentResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class ProcessMessageRequest(BaseModel):
    """Request para processar mensagem"""
    message: str = Field(..., description="Mensagem do usuário")
    conversation_id: str = Field(..., description="ID da conversa")
    user_phone: str = Field(..., description="Telefone do usuário")
    user_name: Optional[str] = Field(None, description="Nome do usuário")
    group_id: Optional[str] = Field(None, description="ID do grupo (se for grupo)")
    is_group: bool = Field(False, description="Se é mensagem de grupo")
    offer_id: Optional[str] = Field(None, description="ID da oferta (se houver)")
    language: str = Field("pt-BR", description="Idioma preferido")
    agent_role: str = Field("vendedor", description="Papel do agente")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais")


class ProcessMessageResponse(BaseModel):
    """Response do processamento"""
    success: bool
    message: str = Field(..., description="Resposta do agente")
    action: Optional[str] = Field(None, description="Ação sugerida")
    data: Optional[Dict[str, Any]] = Field(None, description="Dados adicionais")
    should_continue: bool = Field(True, description="Se a conversa deve continuar")
    agent_role: str = Field(..., description="Papel do agente usado")
    capabilities: list = Field(..., description="Capacidades do agente")


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/process-message",
    response_model=ProcessMessageResponse,
    summary="Processa mensagem WhatsApp",
    description="Processa mensagem do WhatsApp usando agente ágnosto configurável"
)
async def process_message_endpoint(
    request: ProcessMessageRequest,
    _: bool = Depends(verify_api_key)
):
    """
    Processa uma mensagem do WhatsApp usando agente ágnosto.
    
    O agente pode assumir diferentes papéis (vendedor, atendente, etc.)
    e processa a mensagem de forma natural e contextualizada.
    """
    try:
        # Determinar papel do agente
        try:
            agent_role = AgentRole(request.agent_role.lower())
        except ValueError:
            logger.warning(f"Papel de agente inválido: {request.agent_role}, usando 'vendedor'")
            agent_role = AgentRole.VENDEDOR
        
        # Criar contexto
        context = AgentContext(
            conversation_id=request.conversation_id,
            user_phone=request.user_phone,
            user_name=request.user_name,
            group_id=request.group_id,
            is_group=request.is_group,
            offer_id=request.offer_id,
            language=request.language,
            metadata=request.metadata or {}
        )
        
        # Criar agente
        agent_config = {
            "language": request.language,
            "confirm_style": "natural",
            "suggestion_level": "careful"
        }
        agent = AgentFactory.create_agent(agent_role, agent_config)
        
        # Processar mensagem
        logger.info(f"Processando mensagem de {request.user_phone} com agente {agent_role.value}")
        response: AgentResponse = agent.process_message(request.message, context)
        
        # Retornar resposta
        return ProcessMessageResponse(
            success=True,
            message=response.message,
            action=response.action,
            data=response.data,
            should_continue=response.should_continue,
            agent_role=agent_role.value,
            capabilities=agent.get_capabilities()
        )
    
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar mensagem: {str(e)}"
        )


@router.get(
    "/agent/capabilities",
    summary="Lista capacidades do agente",
    description="Retorna lista de capacidades disponíveis para um papel de agente"
)
async def get_agent_capabilities(
    role: str = "vendedor",
    _: bool = Depends(verify_api_key)
):
    """
    Retorna capacidades disponíveis para um papel de agente.
    """
    try:
        agent_role = AgentRole(role.lower())
        agent = AgentFactory.create_agent(agent_role)
        
        return {
            "success": True,
            "role": role,
            "capabilities": agent.get_capabilities()
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Papel de agente inválido: {role}"
        )
    except Exception as e:
        logger.error(f"Erro ao obter capacidades: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter capacidades: {str(e)}"
        )


@router.get(
    "/agent/roles",
    summary="Lista papéis disponíveis",
    description="Retorna lista de papéis de agentes disponíveis"
)
async def get_agent_roles(
    _: bool = Depends(verify_api_key)
):
    """
    Retorna lista de papéis de agentes disponíveis.
    """
    return {
        "success": True,
        "roles": [role.value for role in AgentRole]
    }

