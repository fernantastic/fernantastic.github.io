@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "BASH_EXE="
set "PATH_BASH="

if exist "%ProgramFiles%\Git\bin\bash.exe" set "BASH_EXE=%ProgramFiles%\Git\bin\bash.exe"
if not defined BASH_EXE if exist "%ProgramFiles(x86)%\Git\bin\bash.exe" set "BASH_EXE=%ProgramFiles(x86)%\Git\bin\bash.exe"
if not defined BASH_EXE if exist "%LocalAppData%\Programs\Git\bin\bash.exe" set "BASH_EXE=%LocalAppData%\Programs\Git\bin\bash.exe"
if not defined BASH_EXE (
  for %%I in (bash.exe) do set "PATH_BASH=%%~$PATH:I"
  if defined PATH_BASH if /I not "%PATH_BASH%"=="%SystemRoot%\System32\bash.exe" set "BASH_EXE=%PATH_BASH%"
)

if not defined BASH_EXE (
  echo Git Bash was not found. Install Git for Windows or add its bash.exe to PATH.>&2
  exit /b 1
)

"%BASH_EXE%" "%SCRIPT_DIR%prepare-static-assets.sh" %*
exit /b %ERRORLEVEL%
