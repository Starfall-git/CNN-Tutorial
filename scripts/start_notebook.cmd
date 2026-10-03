@echo off
setlocal
cd /d "%~dp0.."
if exist "D:\WORK\env\anaconda3\condabin\conda.bat" (
    call "D:\WORK\env\anaconda3\condabin\conda.bat" activate CNN-Tutorial
) else (
    call conda activate CNN-Tutorial
)
if errorlevel 1 exit /b 1
python -m notebook notebooks
