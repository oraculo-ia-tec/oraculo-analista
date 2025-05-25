@echo off
echo Iniciando a API do Oráculo Analista (ASAAS)...
cd /d %~dp0

REM Ativa o ambiente virtual, se necessário
call .venv\Scripts\activate

REM Executa a API com Uvicorn
uvicorn api_asaas:app --reload

pause

