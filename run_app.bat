@echo off
echo ==========================================
echo    Iniciando o Video Summarizer IA...
echo ==========================================
echo.
echo Por favor, aguarde enquanto o servidor carrega. 
echo O seu navegador deve abrir automaticamente em instantes!
echo.

cd /d "%~dp0"
.\.venv\Scripts\streamlit.exe run app.py

pause
