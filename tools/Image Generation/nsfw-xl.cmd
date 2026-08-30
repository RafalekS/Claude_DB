@echo off
cd "C:\Users\Raf\Documents\Python\Gradio"
start /b cmd /k python nsfw-xl.py
timeout /t 14 /nobreak >nul
start brave.exe "http://192.168.0.26:16565"
