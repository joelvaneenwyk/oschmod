@echo off
goto:$Main

:Command
    goto:$CommandVar
    :CommandVar
        setlocal EnableDelayedExpansion
        set "_command=!%~1!"
        set "_command=!_command:      = !"
        set "_command=!_command:    = !"
        set "_command=!_command:   = !"
        set "_command=!_command:  = !"
        set _error_value=0
        if "%CRITICAL_ERROR%"=="" goto:$RunCommand
        if "%CRITICAL_ERROR%"=="0" goto:$RunCommand

        :: Hit critical error so skip the command
        echo [ERROR] Critical error detected. Skipped command: !_command!
        set _error_value=%CRITICAL_ERROR%
        goto:$CommandDone

        :$RunCommand
        echo ##[cmd] !_command!
        call !_command!
        set _error_value=%ERRORLEVEL%

        :$CommandDone
        endlocal & (
            exit /b %_error_value%
        )
    :$CommandVar
setlocal EnableDelayedExpansion
    set "_command=%*"
    call :CommandVar "_command"
endlocal & (
    exit /b %ERRORLEVEL%
)

:UpdateRequirements
    setlocal EnableDelayedExpansion
    set "_args="
    set "_filename="
    set "_group=%~1"

    if "!_group!"=="all" goto:$UpdateRequirementsAll
    if "!_group!"=="" goto:$UpdateRequirementsAll

    :: Default
    set "_filename=%~dp0requirements\!_group!.txt"
    set "_args=--extra !_group!"
    goto:$Update

    :: All
    :$UpdateRequirementsAll
    set "_filename=%~dp0requirements.txt"
    set "_args=--all-extras"
    goto:$Update

    :$Update
    call :Command pipx run --spec pip-tools pip-compile ^
        --allow-unsafe --build-isolation --verbose ^
        --strip-extras --no-header --emit-find-links --newline LF ^
        !_args! -o "!_filename!" ^
        "%~dp0pyproject.toml"
endlocal & exit /b %ERRORLEVEL%

:$Main
setlocal EnableExtensions
    set "_root=%~dp0"
    set "_activate=%_root%\venv\Scripts\activate.bat"
    set "_deactivate=%_root%\venv\Scripts\activate.bat"
    set "_pyenv_bin=%USERPROFILE%\.pyenv\pyenv-win\bin"
    set "_pyenv_cmd=%_pyenv_bin%\bin\pyenv.bat"

    if exist "%_activate%" call :Command "%_activate%"

    call pyenv --version >nul 2>&1
    if errorlevel 1 goto:$PyEnvInit
    goto:$PyEnvSetup

    :$PyEnvInit
    set "PATH=%_pyenv%\bin;%PATH%"
    call pyenv --version >nul 2>&1
    if errorlevel 1 goto:$SkipPyEnv
    goto:$PyEnvSetup

    :$PyEnvSetup
    call pyenv install 2.7.18
    call pyenv install 3.8.10
    call pyenv install 3.12.1
    goto:$SkipPyEnv

    :$SkipPyEnv
    goto:$MainUpdate

    :$MainUpdate
    call :UpdateRequirements all
    if errorlevel 1 goto:$MainError

    call :UpdateRequirements ci
    if errorlevel 1 goto:$MainError

    call :UpdateRequirements lint
    if errorlevel 1 goto:$MainError

    call :UpdateRequirements pip
    if errorlevel 1 goto:$MainError

    call :UpdateRequirements release
    if errorlevel 1 goto:$MainError

    call :UpdateRequirements test
    if errorlevel 1 goto:$MainError

    call :Command "%~dp0.venv\Scripts\activate.bat"
    call :Command py -3 -m pip uninstall -y pipywin32 pywin32
    call :Command py -3 -m pip install --user -e ".[dev,test,types,ci,lint,pip,release]"
    if errorlevel 1 goto:$MainError

    if exist "%~dp0Scripts\pywin32_postinstall.py" (
        call :Command py -3 "%~dp0Scripts\pywin32_postinstall.py" -install
    )
    goto:$MainDone

    :$MainError
    echo [ERROR] Failed to setup Python environment for 'oschmod' project. Return code: "%ERRORLEVEL%"
    goto:$MainDone

    :$MainDone
    echo [INFO] Setup completed for 'oschmod' package.
endlocal & exit /b %ERRORLEVEL%
