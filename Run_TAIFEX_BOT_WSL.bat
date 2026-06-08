@echo off
setlocal
title TAIFEX_BOT Launcher

REM Put this BAT file in the TAIFEX_BOT project root folder.
REM Example:
REM D:\AI_PROJECTS\TAIFEX_BOT\Run_TAIFEX_BOT_WSL.bat
REM It will auto open WSL, enter current folder, install requirements, and run main_gui.py.

set "WIN_DIR=%~dp0"

for /f "delims=" %%I in ('wsl wslpath "%WIN_DIR%"') do set "WSL_DIR=%%I"

echo ========================================
echo TAIFEX_BOT Launcher
echo ========================================
echo Windows folder:
echo %WIN_DIR%
echo.
echo WSL folder:
echo %WSL_DIR%
echo.

wsl bash -lc "cd '%WSL_DIR%' && if [ -d current ]; then cd current; fi; if [ -f requirements.txt ]; then pip3 install --break-system-packages -r requirements.txt; fi; python3 main_gui.py"

echo.
echo Program closed.
pause
endlocal
