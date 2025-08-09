
@echo off
echo Instalando CLI Download ROM...

set "INSTALL_DIR=%USERPROFILE%\clidownrom"
set "EXE_PATH=%~dp0clidownrom.exe"

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy "%EXE_PATH%" "%INSTALL_DIR%\"

echo Adicionando ao PATH...
setx PATH "%PATH%;%INSTALL_DIR%"

echo.
echo ✅ Instalação concluída!
echo Reinicie o terminal para usar o comando 'clidownrom'
echo.
pause
