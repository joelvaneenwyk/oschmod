@echo off
goto:$Main

:$Main
setlocal EnableExtensions
    set _root=%~dp0
    set _activate=%_root%\venv\Scripts\activate.bat
    if exist "%_activate%" call "%_activate%"

    set "_pyenv_bin=%USERPROFILE%\.pyenv\pyenv-win\bin"
    set "_pyenv_cmd=%_pyenv_bin%\bin\pyenv.bat"

    call pyenv --version >nul 2>&1
    if errorlevel 1 goto:$PyEnvInit
    goto:$PyEnvSetup

    :$PyEnvInit
    set "PATH=%_pyenv%\bin;%PATH%"
    call pyenv --version >nul 2>&1
    if not exist "%_pyenv_cmd%" goto:$SkipPyEnv

    call pyenv --version >nul 2>&1
    if errorlevel 1 goto:$SkipPyEnv
    call pyenv init --path

    :$PyEnvSetup
    goto:$SkipPyEnv

    :$SkipPyEnv
    goto:$MainDone

    :$MainError
    echo [ERROR] Failed to setup Python environment for 'oschmod' project.
    goto:$MainDone

    :$MainDone
    call py -3 %*
endlocal & (
    set "PATH=%PATH%"
    exit /b %ERRORLEVEL%
)
