@echo off
rem Yiwu Elevation Growth Lab: rebuild index.html from src\ (if Python is available), then open it.
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (
  python build.py
  if errorlevel 1 echo Build failed - opening the last built page instead.
) else (
  echo Python not found - opening the last built page.
)
start "" "%~dp0index.html"
