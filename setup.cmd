::@echo off
goto:$Main

:Command
    goto:$CommandVar
    :CommandVar
        setlocal EnableDelayedExpansion
        set "_command_value=!%~1!"
        set "_command_value=!_command_value:      = !"
        set "_command_value=!_command_value:    = !"
        set "_command_value=!_command_value:   = !"
        set "_command_value=!_command_value:  = !"
        set _error_value=0
        if "%CRITICAL_ERROR%"=="" goto:$RunCommand
        if "%CRITICAL_ERROR%"=="0" goto:$RunCommand

        :: Hit critical error so skip the command
        echo [ERROR] Critical error detected. Skipped command: !_command_value!
        set _error_value=%CRITICAL_ERROR%
        goto:$CommandDone

        :$RunCommand
        echo ##[cmd] !_command_value!
        call !_command_value!
        set _error_value=%ERRORLEVEL%

        :$CommandDone
        endlocal & (
            exit /b %_error_value%
        )
    :$CommandVar
setlocal EnableDelayedExpansion
    set "_command_var=%*"
    call :CommandVar "_command_var"
endlocal & (
    exit /b %ERRORLEVEL%
)

:PipCompile
setlocal EnableExtensions
    cd /d "%~dp0"
    call :Command pipx run ^
        --python "%USERPROFILE%\.pyenv\pyenv-win\shims\python.bat" ^
        --spec pip-tools ^
        pip-compile ^
            --build-isolation ^
            --verbose ^
            --strip-extras ^
            --newline LF ^
            --no-allow-unsafe ^
            --no-reuse-hashes ^
            --no-emit-trusted-host ^
            --no-emit-options ^
            --no-emit-find-links ^
            %* ^
            "pyproject.toml"
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
    :$UpdateRequirementsGroup
    set "_filename=requirements/!_group!.txt"
    set "_args=--extra !_group!"
    goto:$RunUpdateRequirements

    :: All
    :$UpdateRequirementsAll
    set "_filename=requirements.txt"
    set "_args=--all-extras"
    goto:$RunUpdateRequirements

    :$RunUpdateRequirements
    set "_python=%USERPROFILE%\.pyenv\pyenv-win\shims\python.bat"
    if not exist "%_python%" set "_python=python"

    call :PipCompile !_args! -o "!_filename!"
endlocal & exit /b %ERRORLEVEL%

:UpdateRequirementFiles
    setlocal EnableDelayedExpansion
    for %%t in (all ci lint release test) do (
        call :UpdateRequirements %%t
        if errorlevel 1 goto:$UpdateRequirementFilesError
    )
    goto:$UpdateRequirementFilesDone

    :$UpdateRequirementFilesError
        echo [ERROR] Failed to update requirements files.
        goto:$UpdateRequirementFilesDone

    :$UpdateRequirementFilesDone
endlocal & (
    exit /b %ERRORLEVEL%
)

:$Main
setlocal EnableDelayedExpansion
    set "_root=%~dp0"
    set "_activate=%_root%\venv\Scripts\activate.bat"
    set "_deactivate=%_root%\venv\Scripts\activate.bat"
    set "_pyenv_bin=%USERPROFILE%\.pyenv\pyenv-win\bin"
    set "_pyenv_cmd=pyenv"

    :$PyEnvInit1
    call !_pyenv_cmd! --version >nul 2>&1
    if "%ERRORLEVEL%"=="0" goto:$PyEnvSetup

    set "_pyenv_cmd="%_pyenv_bin%\pyenv.bat""
    call !_pyenv_cmd! --version >nul 2>&1
    if "%ERRORLEVEL%"=="0" (
        set "PATH=%_pyenv_bin%;%PATH%"
        goto:$PyEnvSetup
    )
    echo [ERROR] Failed to find and setup 'pyenv' command.
    goto:$MainUpdate

    :$PyEnvSetup
    call :Command !_pyenv_cmd! install --skip-existing --64only "2.7.18" "3.8.10" "3.12.1"
    goto:$MainUpdate

    :$MainUpdate
    call :UpdateRequirementFiles
    if errorlevel 1 goto:$MainError

    if exist "%_activate%" call :Command "%_activate%"
    call :Command py -3 -m pip uninstall -y pipywin32 pywin32
    call :Command py -3 -m pip install --user -e ".[dev,test,types,ci,lint,release]"
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
