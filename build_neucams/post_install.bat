@echo off
setlocal EnableDelayedExpansion
echo === NeuCams post_install ===

:: 0) Ensure %PREFIX% is set
if not defined PREFIX set "PREFIX=%~dp0.."

:: 1) Unpack payload.zip
if exist "%PREFIX%\payload.zip" (
    echo Extracting payload.zip …
    "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -Command ^
      "Expand-Archive -LiteralPath '%PREFIX%\payload.zip' -DestinationPath '%PREFIX%' -Force"
    del "%PREFIX%\payload.zip" >nul 2>&1
)

:: 2) GenTL env_var logic (unchanged, but NEVER exit with error)
set "GVAR=GENICAM_GENTL64_PATH"
for /f "tokens=2,*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v %GVAR% 2^>nul') do set "GENTL=%%B"
if not defined GENTL set "GENTL=%GENICAM_GENTL64_PATH%"

set "MV_DIR=%MVIMPACT_ACQUIRE_DIR%"
set "AV_DIR=%VIMBAX_HOME%"

echo %GVAR%   : %GENTL%
echo MVIMPACT : %MV_DIR%
echo VIMBAX   : %AV_DIR%
echo.

set FOUND_MV=0
set FOUND_AV=0

if defined GENTL (
    for %%P in (!GENTL:;= !) do (
        if exist "%%~P\mvGenTL_Acquire*.cti" set FOUND_MV=1
        if exist "%%~P\VimbaX*.cti"          set FOUND_AV=1
    )
)

set "MYGENTL=%PREFIX%\gentl"
if exist "%MYGENTL%" (
    if !FOUND_MV! == 0 if exist "%MYGENTL%\mvGenTL_Acquire*.cti" set FOUND_MV=1
    if !FOUND_AV! == 0 if exist "%MYGENTL%\VimbaX*.cti"          set FOUND_AV=1

    echo !GENTL! | find /i "%MYGENTL%" >nul
    if errorlevel 1 (
        if defined GENTL (
            set "NEWGENTL=%MYGENTL%;!GENTL!"
        ) else (
            set "NEWGENTL=%MYGENTL%"
        )
        echo Adding %MYGENTL% to %GVAR% (machine scope) …
        setx %GVAR% "!NEWGENTL!" /M >nul 2>&1
        if errorlevel 1 echo [WARN] Could not set machine_wide %GVAR% (non_admin install).
        set "GENTL=!NEWGENTL!"
    )
)

echo.
if !FOUND_MV! == 1 (
    echo [OK] mvIMPACT GenTL found.
) else (
    echo [WARN] mvIMPACT GenTL not found. Install/repair mvIMPACT Acquire.
)

if !FOUND_AV! == 1 (
    echo [OK] Allied Vision GenTL found.
) else (
    echo [WARN] Vimba X GenTL not found. Install/repair Vimba X.
)

if not defined MV_DIR echo [WARN] MVIMPACT_ACQUIRE_DIR not set (drivers/tools may be missing).
if not defined AV_DIR echo [WARN] VIMBAX_HOME not set (SDK path missing).

echo.
echo === Post_install done ===

:: ------------------------------------------------------------------
:: Reset ERRORLEVEL so Constructor sees success
:: ------------------------------------------------------------------
cmd /c exit 0
endlocal & exit /b 0
