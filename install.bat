@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "PYTHON_BIN="
where python >nul 2>nul && set "PYTHON_BIN=python"
if not defined PYTHON_BIN (
    where py >nul 2>nul && set "PYTHON_BIN=py"
)
if not defined PYTHON_BIN (
    echo python is required
    exit /b 1
)

echo [1/1] install yunxiao_cli package
%PYTHON_BIN% -m pip install -e "%SCRIPT_DIR%"
if errorlevel 1 exit /b 1

echo done
echo yunxiao_cli --help
echo.
echo Need install skill? run:
echo   install_skill.bat
