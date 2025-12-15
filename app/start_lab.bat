@echo off
cd /d %~dp0
set TELEMETRY_ENV=lab
echo ==================================================
echo   STARTING CNC TELEMETRY IN LAB MODE (SIMULATION)
echo ==================================================
powershell -ExecutionPolicy Bypass -File scripts\start_telemetry_demo.ps1
