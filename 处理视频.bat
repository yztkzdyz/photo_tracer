@echo off
cd /d "%~dp0"

set "VID=%~1"
if "%VID%"=="" (
    echo 把视频或整个文件夹拖到本文件图标上，或在下面输入路径：
    echo （文件夹会自动处理里面所有 mp4/avi/mov/mkv 视频）
    set /p VID=视频或文件夹路径：
)

if not exist "%VID%" (
    echo 找不到文件: %VID%
    pause
    exit /b 1
)

set "FAIL=0"
set "ISDIR=0"
if exist "%VID%\*" set "ISDIR=1"

if "%ISDIR%"=="1" goto :dodir
call :one "%VID%"
goto :done

:dodir
echo 检测到文件夹，处理其中所有视频...
for %%F in ("%VID%\*.mp4") do call :one "%%~fF"
for %%F in ("%VID%\*.avi") do call :one "%%~fF"
for %%F in ("%VID%\*.mov") do call :one "%%~fF"
for %%F in ("%VID%\*.mkv") do call :one "%%~fF"
goto :done

:one
if not exist "%~1" exit /b 0
echo.
echo ====== 正在处理: %~nx1 ======
".venv\Scripts\python.exe" process_video.py --input "%~1" --device GPU
if errorlevel 1 set "FAIL=1"
exit /b 0

:done
echo.
if not "%FAIL%"=="0" (
    echo 部分视频处理失败，请把上面的报错信息反馈。
    pause
    exit /b 1
)
echo 全部完成！深度视频已保存到 output 文件夹（无音轨）。
if not defined PHOTO_TRACER_NOOPEN start "" "output"
pause
