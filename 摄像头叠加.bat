@echo off
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
