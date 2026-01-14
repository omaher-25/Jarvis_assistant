@echo off
REM Activate the virtual environment and run JARVIS
call .\env\Scripts\activate.bat
python src\full_assistant\main.py
pause