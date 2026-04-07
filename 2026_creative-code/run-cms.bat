@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
where.exe python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python or add it to PATH.>&2
  exit /b 1
)

python -u "%SCRIPT_DIR%cms\server.py" %*
exit /b %ERRORLEVEL%
