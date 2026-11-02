@echo off
title Groww Stitch UI Prototype Server
echo =========================================================================
echo   Starting Groww Stitch UI Prototype Server...
echo   URL: http://localhost:8080
echo =========================================================================
echo.
.venv\Scripts\python.exe app\serve_ui.py 8080
pause

