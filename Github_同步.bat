@echo off
cd /d "%~dp0"

git config --global user.name "jacky4093"
git config --global user.email "jacky4093@gmail.com"

git pull origin main

git add .

set /p MSG=請輸入更新說明:
if "%MSG%"=="" set MSG=update

git commit -m "%MSG%"

git push origin main

pause