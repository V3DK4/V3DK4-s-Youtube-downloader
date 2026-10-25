@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (set "PY=py") else (set "PY=python")
%PY% -m pip install -r requirements.txt
if errorlevel 1 (echo HIBA: Python vagy pip nincs telepitve. & pause & exit /b 1)
echo.
echo Nyisd meg: http://127.0.0.1:5000
echo Ne zard be ezt az ablakot, amig hasznalod az oldalt.
%PY% app.py
pause
