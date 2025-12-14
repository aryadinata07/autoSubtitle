@echo off
REM Auto Subtitle Generator - Global Command
REM This script allows you to run autosub from anywhere

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0

REM Save current directory (where user ran the command)
set USER_DIR=%CD%

REM Set environment variable for Python script to detect
set AUTOSUB_USER_DIR=%USER_DIR%

REM Run Python script with all arguments (don't change directory!)
python "%SCRIPT_DIR%generate_subtitle.py" %*
