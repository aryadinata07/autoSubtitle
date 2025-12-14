@echo off
REM Auto Subtitle Generator - Global Command
REM This script allows you to run autosub from anywhere

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0

REM Change to script directory
cd /d "%SCRIPT_DIR%"

REM Run Python script with all arguments
python "%SCRIPT_DIR%generate_subtitle.py" %*
