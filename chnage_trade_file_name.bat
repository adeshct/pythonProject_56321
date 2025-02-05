setlocal enabledelayedexpansion

for /r %%i in (trades.json) do (
    set "folder=%%~dpi"
    set "folder=!folder:~0,-1!"  REM Removing the trailing backslash from the folder path
    set "filename=%%~nxi"
    ren "%%i" "!folder!-!filename!"
)

endlocal

