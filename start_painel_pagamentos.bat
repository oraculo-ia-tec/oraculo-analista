@echo off
echo Iniciando Painel de Pagamentos do Oráculo Analista...
cd /d %~dp0

REM Ativa o ambiente virtual (ajuste o nome da pasta se necessário)
call .venv\Scripts\activate

REM Executa o Streamlit
streamlit run painel_pagamentos_usuario.py

pause
