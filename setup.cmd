@echo off
setlocal EnableExtensions
call "%~dp0.venv\Scripts\activate.bat"
call py -3 -m pip install --user distutils
call py -3 -m pip uninstall -y pipywin32
call py -3 -m pip uninstall -y pywin32
call py -3 -m pip install --user pywin32>=306
if exist "%~dp0Scripts\pywin32_postinstall.py" (
    call python "%~dp0Scripts\pywin32_postinstall.py" -install
)
