@echo off

cd /d "%~dp0"

git pull origin main

git add .

set /p MSG=請輸入更新說明:

if "%MSG%"=="" set MSG=update

git commit -m "%MSG%"

git push origin main

pause