@echo off
REM Activate the virtual environment and run JARVIS without console
call .\env\Scripts\activate.bat
pythonw src\full_assistant\main.py