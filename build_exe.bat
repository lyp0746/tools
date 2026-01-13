@echo off
chcp 65001 >nul
title 专业工具集EXE打包脚本 - 体积最小化优化

echo ================================================
echo   专业工具集EXE打包脚本
echo   版本: 1.0 | 作者: LYP
echo ================================================
echo.

:: 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python环境，请先安装Python 3.7+
    pause
    exit /b 1
)

:: 检查PyInstaller
pip list | findstr "pyinstaller" >nul
if errorlevel 1 (
    echo [信息] 正在安装PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller安装失败
        pause
        exit /b 1
    )
)

:: 创建构建目录
if not exist "build" mkdir build
if not exist "dist" mkdir dist

echo [信息] 开始打包15个专业工具...

:: ==================== 打包函数定义 ====================
:PackTool
setlocal
set "TOOL_NAME=%~1"
set "PY_FILE=%~2"
set "ICON_FILE=%~3"
set "ADDITIONAL_OPTIONS=%~4"

echo.
echo ===== 正在打包: %TOOL_NAME% =====

:: 检查Python文件是否存在
if not exist "%PY_FILE%" (
    echo [警告] 文件 %PY_FILE% 不存在，跳过
    goto :EOF
)

:: 构建最小化打包命令
set "BUILD_CMD=pyinstaller"
set "BUILD_CMD=%BUILD_CMD% --onefile"                    :: 单文件模式
set "BUILD_CMD=%BUILD_CMD% --windowed"                   :: 无控制台窗口
set "BUILD_CMD=%BUILD_CMD% --noconfirm"                  :: 覆盖确认
set "BUILD_CMD=%BUILD_CMD% --clean"                      :: 清理缓存
set "BUILD_CMD=%BUILD_CMD% --name %TOOL_NAME%"           :: 输出名称

:: 体积优化选项
set "BUILD_CMD=%BUILD_CMD% --exclude-module tkinter"     :: 排除tkinter
set "BUILD_CMD=%BUILD_CMD% --exclude-module matplotlib.tests"
set "BUILD_CMD=%BUILD_CMD% --exclude-module numpy.random._examples"
set "BUILD_CMD=%BUILD_CMD% --exclude-module scipy"
set "BUILD_CMD=%BUILD_CMD% --exclude-module pandas.tests"

:: 压缩选项
set "BUILD_CMD=%BUILD_CMD% --strip"                      :: 去除符号信息
set "BUILD_CMD=%BUILD_CMD% --optimize 2"                 :: 字节码优化

:: 如果有图标文件
if not "%ICON_FILE%"=="" (
    if exist "%ICON_FILE%" (
        set "BUILD_CMD=%BUILD_CMD% --icon %ICON_FILE%"
    )
)

:: 添加额外选项
if not "%ADDITIONAL_OPTIONS%"=="" (
    set "BUILD_CMD=%BUILD_CMD% %ADDITIONAL_OPTIONS%"
)

:: 执行打包
echo [执行] %BUILD_CMD% "%PY_FILE%"
%BUILD_CMD% "%PY_FILE%"

if errorlevel 1 (
    echo [错误] %TOOL_NAME% 打包失败
) else (
    echo [成功] %TOOL_NAME% 打包完成
    :: 移动文件到dist目录
    if exist "dist\%TOOL_NAME%.exe" (
        move "dist\%TOOL_NAME%.exe" "dist\%TOOL_NAME%_v1.0.exe" >nul
        echo [信息] 输出文件: dist\%TOOL_NAME%_v1.0.exe
    )
)

endlocal
goto :EOF

:: ==================== 开始打包各个工具 ====================

:: 1. AutomationToolPro
call :PackTool "AutomationToolPro" "AutomationToolPro\AutomationToolPro.py" ""

:: 2. CodeAnalyzerPro
call :PackTool "CodeAnalyzerPro" "CodeAnalyzerPro\CodeAnalyzerPro.py" ""

:: 3. DataVizPro
call :PackTool "DataVizPro" "DataVizPro\DataVizPro.py" ""

:: 4. DatabaseManagerPro
call :PackTool "DatabaseManagerPro" "DatabaseManagerPro\DatabaseManagerPro.py" ""

:: 5. FinancialCalculatorPro
call :PackTool "FinancialCalculatorPro" "FinancialCalculatorPro\FinancialCalculatorPro.py" ""

:: 6. ImageProcessorPro
call :PackTool "ImageProcessorPro" "ImageProcessorPro\ImageProcessorPro.py" ""

:: 7. NetworkToolPro
call :PackTool "NetworkToolPro" "NetworkToolPro\NetworkToolPro.py" ""

:: 8. SecurityVaultPro
call :PackTool "SecurityVaultPro" "SecurityVaultPro\SecurityVaultPro.py" ""

:: 9. StreamForgeElite
call :PackTool "StreamForgeElite" "StreamForgeElite\StreamForgeElite.py" ""

:: 10. SubMuxOmniPro
call :PackTool "SubMuxOmniPro" "SubMuxOmniPro\SubMuxOmniPro.py" ""

:: 11. SystemMonitorPro
call :PackTool "SystemMonitorPro" "SystemMonitorPro\SystemMonitorPro.py" ""

:: 12. TextProcessorPro
call :PackTool "TextProcessorPro" "TextProcessorPro\TextProcessorPro.py" ""

:: 13. UltimateFileConverter
call :PackTool "UltimateFileConverter" "UltimateFileConverter\UltimateFileConverter.py" ""

:: 14. UltimateReader
call :PackTool "UltimateReader" "UltimateReader\UltimateReader.py" ""

:: 15. UniversalWebCrawlerPro
call :PackTool "UniversalWebCrawlerPro" "UniversalWebCrawlerPro\UniversalWebCrawlerPro.py" ""

:: ==================== 打包完成 ====================
echo.
echo ================================================
echo   打包完成！
echo ================================================
echo.

:: 显示文件大小信息
echo [信息] 生成的EXE文件列表及大小:
echo.
for %%f in (dist\*.exe) do (
    for %%i in (%%f) do (
        set "size=%%~zi"
        set /a "size_mb=!size!/1048576"
        set /a "size_kb=!size!/1024"
        echo   %%~nxf - !size_mb! MB (!size_kb! KB)
    )
)

echo.
echo [提示] 所有EXE文件已保存到 dist\ 目录
echo [提示] 建议在干净的Python虚拟环境中打包以获得最小体积
echo.

pause
