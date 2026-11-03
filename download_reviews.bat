@echo off
title Download Reviews & Comments - Groww SIP Discovery Engine
echo =========================================================================
echo   Downloading Reviews & Comments across Play Store, App Store, YouTube...
echo =========================================================================
echo.
call .venv\Scripts\activate.bat
python scripts\download_more_data.py --play-limit 50 --app-limit 30 --yt-limit 30 --reddit-limit 15 --run-downstream
echo.
echo =========================================================================
echo   Collection, Cleaning, LLM Extraction, and Clustering Completed!
echo =========================================================================
pause
