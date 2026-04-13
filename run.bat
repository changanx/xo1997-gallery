@echo off
chcp 65001 >nul
title xo1997 画廊 - 运行日志
echo ========================================
echo   xo1997 画廊 启动中...
echo ========================================
echo.

cd /d "%~dp0"

.venv\Scripts\python.exe -m app.main

pause
