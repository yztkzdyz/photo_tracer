@echo off
cd /d "%~dp0"

set "IMG=%~1"
if "%IMG%"=="" (
    echo 把图片或整个文件夹拖到本文件图标上，或在下面输入路径：
    echo （文件夹会自动处理里面所有 jpg/png 图片）
    set /p IMG=图片或文件夹路径：
)
if "%IMG%"=="" exit /b 1

set "FAIL=0"
set "ISDIR=0"
if exist "%IMG%\*" set "ISDIR=1"

if "%ISDIR%"=="1" goto :dodir
call :one "%IMG%"
goto :done

:dodir
echo 检测到文件夹，处理其中所有图片...
for %%F in ("%IMG%\*.jpg")  do call :one "%%~fF"
for %%F in ("%IMG%\*.jpeg") do call :one "%%~fF"
for %%F in ("%IMG%\*.png")  do call :one "%%~fF"
for %%F in ("%IMG%\*.webp") do call :one "%%~fF"
goto :done

:one
if not exist "%~1" exit /b 0
echo.
echo ====== 正在处理: %~nx1 ======
".venv\Scripts\python.exe" generate_outline.py --input "%~1" --output "output\%~n1_outline.png" --mode outline --device GPU
if errorlevel 1 set "FAIL=1"
".venv\Scripts\python.exe" generate_outline.py --input "%~1" --output "output\%~n1_lineart.png" --mode lineart --device GPU
if errorlevel 1 set "FAIL=1"
".venv\Scripts\python.exe" generate_depth.py --input "%~1" --device GPU --subject-outline
if errorlevel 1 set "FAIL=1"
exit /b 0

:done
echo.
if not "%FAIL%"=="0" (
    echo 部分文件处理失败，请把上面的报错信息反馈。
    pause
    exit /b 1
)
echo 全部完成！输出文件在 output 文件夹，每个图片对应：
echo   xx_outline.png                 外轮廓
echo   xx_lineart.png                 线稿
echo   xx_depth_subject.png           深度伪彩色
echo   xx_depth_isolines_subject.png  深度等深线+人物轮廓
if not defined PHOTO_TRACER_NOOPEN start "" "output"
pause
