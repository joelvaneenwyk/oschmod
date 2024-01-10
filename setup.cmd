@echo off
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
setlocal EnableDelayedExpansion
    cd /d "%~dp0"
    set "_args="
    set "_pip_compile_standalone=pip-compile"

    set "_pip_compile_pipx=pipx run"
    set "_pip_compile_pipx=!_pip_compile_pipx! --spec pip-tools pip-compile"
    set "_pyenv_python=%USERPROFILE%\.pyenv\pyenv-win\shims\python.bat"
    if exist "%_pyenv_python%" (
        set "_pip_compile_pipx=!_pip_compile_pipx! --python "!_pyenv_python!" "
    )

    set "_pip_compile=!_pip_compile_pipx!"
    call !_pip_compile! --version >nul 2>&1
    if "%ERRORLEVEL%"=="0" goto:$PipCompileCall

    set "_pip_compile=!_pip_compile_standalone!"
    call !_pip_compile! --version >nul 2>&1
    if "%ERRORLEVEL%"=="0" goto:$PipCompileCall
    echo [ERROR] Failed to find 'pip-compile' command.

    :$PipCompileCall
    call :Command !_pip_compile! ^
            --constraint "requirements/constraints.txt" ^
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
    call :PipCompile !_args! -o "!_filename!"
endlocal & exit /b %ERRORLEVEL%

:UpdateRequirementFiles
    setlocal EnableDelayedExpansion
    for %%t in (all ci lint release test types) do (
        call :UpdateRequirements %%t
        if errorlevel 1 goto:$UpdateRequirementFilesError
        if "%%t"=="" goto:$UpdateRequirementFilesError
    )
    goto:$UpdateRequirementFilesDone

    :$UpdateRequirementFilesError
        echo [ERROR] Failed to update requirements files.
        goto:$UpdateRequirementFilesDone

    :$UpdateRequirementFilesDone
endlocal & (
    exit /b %ERRORLEVEL%
)

:GetRoot
    setlocal EnableDelayedExpansion
    set "_root=%~dp0"
    if "%_root:~-1%"=="\" set "_root=%_root:~0,-1%"
endlocal & (
    set "_root=%_root%"
    set "_activate=%_root%\.venv\Scripts\activate.bat"
    set "_deactivate=%_root%\.venv\Scripts\deactivate.bat"
    set "_new_path=%PATH%"
    set "_old_path=%PATH%"
)
echo Root: %_root%
echo Activate: %_activate%
exit /b %ERRORLEVEL%

:InstallEnv
setlocal EnableDelayedExpansion
    if exist "%_activate%" call :Command "%_activate%"
    call :Command py -3 -m pip uninstall -y -r "!_root!\requirements\restricted.txt"
    call :Command py -3 -m pip install --user -e ".[dev,test,types,ci,lint,release]"
    if exist "%~dp0Scripts\pywin32_postinstall.py" (
        call :Command py -3 "%~dp0Scripts\pywin32_postinstall.py" -install
    )
    set "PATH=%_old_path%"
    if exist "%_deactivate%" call :Command "%_deactivate%"
endlocal
exit /b

:$Main
setlocal EnableDelayedExpansion
    set "_setup_command=%~1"
    call :GetRoot

    set "_pyenv_root=%USERPROFILE%\.pyenv\pyenv-win"
    set "_pyenv_bin=%_pyenv_root%\bin"
    set "_pyenv_shims=%_pyenv_root%\shims"
    set "_pyenv_cmd=pyenv"
    call !_pyenv_cmd! --version >nul 2>&1
    if "%ERRORLEVEL%"=="0" goto:$PyEnvSetup

    set "_pyenv_cmd="!_pyenv_root!\bin\pyenv.bat""
    call !_pyenv_cmd! --version >nul 2>&1
    if "%ERRORLEVEL%"=="0" (
        set "_new_path=!_pyenv_root!\bin;!_new_path!"
        goto:$PyEnvSetup
    )
    echo [ERROR] Failed to find and setup 'pyenv' command.
    goto:$MainUpdate

    :$PyEnvSetup
    call :Command !_pyenv_cmd! install ^
        --skip-existing --64only ^
        "2.7.18" ^
        "3.8.10" ^
        "3.12.1"
    call :Command !_pyenv_cmd! local 3.8.10
    if errorlevel 1 goto:$MainError

    where "python3.8" >nul 2>&1
    if errorlevel 1 (
       set "_new_path=!_pyenv_root!\shims;!_new_path!"
    )
    goto:$MainUpdate

    :$MainUpdate
        call :InstallEnv
        if errorlevel 1 goto:$MainError

        if "%_setup_command%"=="update" (
            call :UpdateRequirementFiles
        )
        if errorlevel 1 goto:$MainError
    goto:$MainDone

    :$MainError
    echo [ERROR] Failed to setup Python environment for 'oschmod' project. Return code: "%ERRORLEVEL%"
    goto:$MainDone

    :$MainDone
    echo [INFO] Setup completed for 'oschmod' package.
endlocal & (
    set "PATH=%_new_path%"
)
