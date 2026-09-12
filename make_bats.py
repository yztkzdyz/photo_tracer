# -*- coding: utf-8 -*-
"""把两个 .bat 以 GBK 编码重写（cmd 在中文 Windows 下按 GBK 解析，UTF-8 会乱码）。"""

process = r'''@echo off
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
'''

camera = r'''@echo off
cd /d "%~dp0"

echo 可用的线稿文件：
dir /b "output\*lineart*.png" 2>nul
echo.
echo 输入要叠加的线稿文件名（如 lineart_p1.png），直接回车默认 lineart_p1.png：
set /p F=
if "%F%"=="" set "F=lineart_p1.png"

if not exist "output\%F%" (
    echo 找不到 output\%F%
    pause
    exit /b 1
)

copy /y "output\%F%" "output\outline.png" >nul
echo 已选择 %F%，正在打开摄像头
echo 按键说明：wasd移动  +和-缩放  q/e旋转  [和]调透明度  p截图  ESC退出
".venv\Scripts\python.exe" camera_overlay.py
pause
'''

video = r'''@echo off
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
'''

with open("处理图片.bat", "w", encoding="gbk", newline="\r\n") as f:
    f.write(process)
with open("处理视频.bat", "w", encoding="gbk", newline="\r\n") as f:
    f.write(video)
with open("摄像头叠加.bat", "w", encoding="gbk", newline="\r\n") as f:
    f.write(camera)
print("OK: 三个 bat 已按 GBK 编码生成")
