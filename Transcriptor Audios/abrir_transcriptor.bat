@echo off
set SCRIPT_DIR=%~dp0
set PYTHON_EXE=C:\Users\Lumi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe

if not exist "%PYTHON_EXE%" (
    echo No se encontro el runtime de Python necesario.
    pause
    exit /b 1
)

"%PYTHON_EXE%" "%SCRIPT_DIR%transcribe_audio_gui.py"
