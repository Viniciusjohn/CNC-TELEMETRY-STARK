@echo off
cd /d %~dp0
set TELEMETRY_ENV=field
REM Default Fanuc IP if not set in system
if "%FANUC_HOST%"=="" set FANUC_HOST=192.168.1.100
if "%FANUC_PORT%"=="" set FANUC_PORT=8193

echo ==================================================
echo   STARTING CNC TELEMETRY IN FIELD MODE (REAL DATA)
echo   Target: %FANUC_HOST%:%FANUC_PORT%
echo ==================================================
powershell -ExecutionPolicy Bypass -File scripts\start_telemetry_demo.ps1
