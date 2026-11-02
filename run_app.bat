@echo off
title Groww SIP AI Discovery Engine
echo =========================================================================
echo   Starting Groww SIP AI Discovery Engine (Streamlit Dashboard)...
echo   URL: http://localhost:8501
echo =========================================================================
echo.
call .venv\Scripts\activate.bat
streamlit run app\streamlit_app.py
pause

