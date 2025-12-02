#!/bin/bash
# Script para iniciar o servidor OpenMind AI

# Ativar ambiente virtual
source venv/bin/activate

# Executar servidor
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --log-level info
