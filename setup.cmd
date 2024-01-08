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
        !_args! -o "!_filename!" ^
        "%~dp0pyproject.toml"
endlocal & exit /b %ERRORLEVEL%

:$Main
setlocal EnableExtensions
    call :Command "%~dp0.venv\Scripts\deactivate.bat"
    call :UpdateRequirements all
    call :UpdateRequirements ci
    call :UpdateRequirements lint
    call :UpdateRequirements pip
    call :UpdateRequirements release
    call :UpdateRequirements test

    call :Command "%~dp0.venv\Scripts\activate.bat"
    call :Command py -3 -m pip uninstall -y pipywin32 pywin32
    call :Command py -3 -m pip install --user -e ".[dev,test,types,ci,lint,pip,release]"

    if exist "%~dp0Scripts\pywin32_postinstall.py" (
        call :Command py -3 "%~dp0Scripts\pywin32_postinstall.py" -install
    )
endlocal & exit /b %ERRORLEVEL%
