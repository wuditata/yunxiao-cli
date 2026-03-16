@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "SKILL_NAME=yunxiao-workflow"
set "SKILL_SOURCE=%SCRIPT_DIR%\skills\%SKILL_NAME%"
set "AGENTS_SKILLS_DIR=%USERPROFILE%\.agents\skills"

set "PYTHON_BIN="
where python >nul 2>nul && set "PYTHON_BIN=python"
if not defined PYTHON_BIN (
    where py >nul 2>nul && set "PYTHON_BIN=py"
)
if not defined PYTHON_BIN (
    echo python is required
    exit /b 1
)

echo [1/2] install python package
%PYTHON_BIN% -m pip install -e "%SCRIPT_DIR%"
if errorlevel 1 exit /b 1

echo [2/2] install skill
call :copy_skill "%SKILL_SOURCE%" "%AGENTS_SKILLS_DIR%\%SKILL_NAME%"
if errorlevel 1 exit /b 1
call :copy_skill "%AGENTS_SKILLS_DIR%\%SKILL_NAME%" "%USERPROFILE%\.config\agents\skills\%SKILL_NAME%"
if errorlevel 1 exit /b 1
call :copy_skill "%AGENTS_SKILLS_DIR%\%SKILL_NAME%" "%USERPROFILE%\.codex\skills\%SKILL_NAME%"
if errorlevel 1 exit /b 1
call :copy_skill "%AGENTS_SKILLS_DIR%\%SKILL_NAME%" "%USERPROFILE%\.claude\skills\%SKILL_NAME%"
if errorlevel 1 exit /b 1
call :copy_skill "%AGENTS_SKILLS_DIR%\%SKILL_NAME%" "%USERPROFILE%\.gemini\skills\%SKILL_NAME%"
if errorlevel 1 exit /b 1

echo done
echo yunxiao_cli --help
exit /b 0

:copy_skill
set "SOURCE=%~1"
set "TARGET=%~2"
for %%D in ("%TARGET%\..") do if not exist "%%~fD" mkdir "%%~fD"
if exist "%TARGET%" rmdir /s /q "%TARGET%" >nul 2>nul
if exist "%TARGET%" del /f /q "%TARGET%" >nul 2>nul
xcopy "%SOURCE%" "%TARGET%" /E /I /Y >nul
exit /b %errorlevel%
