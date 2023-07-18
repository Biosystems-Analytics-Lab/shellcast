@echo off
set cwd=%~dp0
pushd %cwd%
echo %cd%

:: Kill process if cloud-sql-proxy is running
QPROCESS "cloud-sql-proxy.exe">NUL
IF %ERRORLEVEL% EQU 0 taskkill /f /im cloud-sql-proxy.exe

set nc_main=%cwd%main_pqpf_nc.py
set sc_main=%cwd%main_pqpf_sc.py


start cmd /k call sqlauthproxy.bat
timeout /t 15
call activate pqpf
python %nc_main%
python %sc_main%
call conda deactivate
timeout /t 15
taskkill /f /im cloud-sql-proxy.exe
taskkill /fi "WindowTitle eq sqlauthproxy*" /t /f
