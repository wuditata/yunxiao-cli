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

echo [1/2] install yunxiao package
%PYTHON_BIN% -m pip install -e "%SCRIPT_DIR%"
if errorlevel 1 exit /b 1

echo [2/2] install yunxiao skill
call "%SCRIPT_DIR%\install_skill.bat"
if errorlevel 1 exit /b 1

echo done
echo yunxiao --help
echo legacy command remains available:
echo   yunxiao_cli --help
