@echo off
rem Yiwu Elevation Growth Lab: rebuild the page from the template (if Python is available), then open it.
rem Opened from disk, it shares the Podium Lab's saved state when both are opened in the same browser.
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (
  python build.py
  if errorlevel 1 echo Build failed - opening the last built page instead.
) else (
  echo Python not found - opening the last built page.
)
start "" "%~dp0Yiwu Elevation Growth Lab.html"
