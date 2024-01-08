@echo off
setlocal EnableExtensions
    call "%~dp0.venv\Scripts\activate.bat"
    call py -3 -m pip uninstall -y pipywin32 pywin32
    call py -3 -m pip install --user -e ".[dev,test,types,ci,lint,pip,release]"

    if exist "%~dp0Scripts\pywin32_postinstall.py" (
        call py -3 "%~dp0Scripts\pywin32_postinstall.py" -install
    )

    call "%~dp0.venv\Scripts\deactivate.bat"
    pipx run --spec pip-tools pip-compile ^
        --all-extras --build-isolation --verbose ^
        -o "%~dp0requirements.txt" ^
        "%~dp0pyproject.toml"

    pipx run --spec pip-tools pip-compile ^
        --extras=ci --build-isolation --verbose ^
        -o "%~dp0requirements\ci.txt" ^
        "%~dp0pyproject.toml"
endlocal & exit /b %ERRORLEVEL%
